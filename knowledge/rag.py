"""
LangChain RAG with Hybrid Search.

Hybrid Search:
    1. BM25 Keyword Search
    2. Qdrant Semantic Search
    3. RRF Fusion

Keyword Search + Semantic Search
                ↓
              RRF
                ↓
        Final relevant documents
"""

import os
import json
import re

from qdrant_client import QdrantClient

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

from rank_bm25 import BM25Okapi


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(__file__)

KB_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "knowledge_base.json",
)

DB_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "qdrant_store_langchain",
)

COLLECTION_NAME = "appinsnap_kb_lc"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ============================================================
# GLOBAL VARIABLES
# ============================================================

_vectorstore = None

_knowledge_base = None

_bm25 = None

_tokenized_documents = None


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def _load_knowledge_base():
    """
    Load knowledge_base.json and create the BM25 keyword index.

    This function runs only once.
    """

    global _knowledge_base
    global _bm25
    global _tokenized_documents

    # --------------------------------------------------------
    # If already loaded, don't load it again
    # --------------------------------------------------------

    if _knowledge_base is not None:
        return

    # --------------------------------------------------------
    # Load JSON knowledge base
    # --------------------------------------------------------

    with open(
        KB_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        _knowledge_base = json.load(f)

    # --------------------------------------------------------
    # Combine topic + content
    # --------------------------------------------------------

    documents = [
        f"{item['topic']} {item['content']}"
        for item in _knowledge_base
    ]

    # --------------------------------------------------------
    # Tokenize documents
    # --------------------------------------------------------

    _tokenized_documents = [
        re.findall(
            r"\b\w+\b",
            document.lower()
        )
        for document in documents
    ]

    # --------------------------------------------------------
    # Create BM25 index
    # --------------------------------------------------------

    _bm25 = BM25Okapi(
        _tokenized_documents
    )


# ============================================================
# GET QDRANT VECTOR STORE
# ============================================================

def _get_vectorstore():
    """
    Create and return the Qdrant vector store.

    It is created only once and then reused.
    """

    global _vectorstore

    # --------------------------------------------------------
    # Reuse existing vector store
    # --------------------------------------------------------

    if _vectorstore is not None:
        return _vectorstore

    # --------------------------------------------------------
    # Check database
    # --------------------------------------------------------

    if not os.path.exists(DB_PATH):

        raise RuntimeError(
            "Vector database not found. Run this first:\n"
            "  python langchain_version/build_vector_db_lc.py"
        )

    # --------------------------------------------------------
    # Connect to Qdrant
    # --------------------------------------------------------

    client = QdrantClient(
        path=DB_PATH
    )

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    # --------------------------------------------------------
    # Connect LangChain to Qdrant
    # --------------------------------------------------------

    _vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    return _vectorstore


# ============================================================
# KEYWORD SEARCH - BM25
# ============================================================

def _keyword_search(
    query: str,
    top_k: int = 5,
):
    """
    Search the knowledge base using keywords.

    BM25 checks how strongly the query words
    match each document.
    """

    # --------------------------------------------------------
    # Load BM25
    # --------------------------------------------------------

    _load_knowledge_base()

    # --------------------------------------------------------
    # Convert query into words
    # --------------------------------------------------------

    query_tokens = re.findall(
        r"\b\w+\b",
        query.lower()
    )

    # --------------------------------------------------------
    # Get BM25 score for every document
    # --------------------------------------------------------

    scores = _bm25.get_scores(
        query_tokens
    )

    # --------------------------------------------------------
    # Sort document indexes by score
    # Highest score first
    # --------------------------------------------------------

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )

    results = []

    # --------------------------------------------------------
    # Take top documents
    # --------------------------------------------------------

    for index in ranked_indices[:top_k]:

        score = float(
            scores[index]
        )

        # Ignore documents with no keyword match
        if score <= 0:
            continue

        item = _knowledge_base[index]

        results.append(
            {
                "id": item["id"],
                "topic": item["topic"],
                "content": item["content"],
                "keyword_score": score,
            }
        )

    return results


# ============================================================
# SEMANTIC SEARCH - QDRANT
# ============================================================

def _semantic_search(
    query: str,
    top_k: int = 5,
):
    """
    Search Qdrant using semantic similarity.
    """

    # --------------------------------------------------------
    # Get Qdrant vector store
    # --------------------------------------------------------

    vs = _get_vectorstore()

    # --------------------------------------------------------
    # Search Qdrant
    # --------------------------------------------------------

    docs_with_scores = (
        vs.similarity_search_with_score(
            query,
            k=top_k,
        )
    )

    results = []

    # --------------------------------------------------------
    # Process Qdrant results
    # --------------------------------------------------------

    for doc, score in docs_with_scores:

        score = round(
            float(score),
            3
        )

        results.append(
            {
                "id": doc.metadata.get(
                    "id",
                    "",
                ),

                "topic": doc.metadata.get(
                    "topic",
                    "",
                ),

                "content": doc.metadata.get(
                    "content",
                    doc.page_content,
                ),

                "semantic_score": score,
            }
        )

    return results


# ============================================================
# RRF FUSION
# ============================================================

def _rrf_fusion(
    keyword_results,
    semantic_results,
    top_k=3,
):
    """
    Combine BM25 and semantic search rankings
    using Reciprocal Rank Fusion (RRF).
    """

    # --------------------------------------------------------
    # RRF constant
    # --------------------------------------------------------

    RRF_K = 60

    # Dictionary containing combined documents
    fused = {}

    # ========================================================
    # ADD KEYWORD RESULTS
    # ========================================================

    for rank, result in enumerate(
        keyword_results,
        start=1
    ):

        document_id = result["id"]

        # Create document if not already present
        if document_id not in fused:

            fused[document_id] = {
                "id": document_id,
                "topic": result["topic"],
                "content": result["content"],
                "rrf_score": 0.0,
            }

        # Add RRF score
        fused[document_id]["rrf_score"] += (
            1 / (RRF_K + rank)
        )

    # ========================================================
    # ADD SEMANTIC RESULTS
    # ========================================================

    for rank, result in enumerate(
        semantic_results,
        start=1
    ):

        document_id = result["id"]

        # Create document if not already present
        if document_id not in fused:

            fused[document_id] = {
                "id": document_id,
                "topic": result["topic"],
                "content": result["content"],
                "rrf_score": 0.0,
            }

        # Add RRF score
        fused[document_id]["rrf_score"] += (
            1 / (RRF_K + rank)
        )

    # ========================================================
    # SORT FINAL RESULTS
    # ========================================================

    ranked_results = sorted(
        fused.values(),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )

    # ========================================================
    # FORMAT SCORE
    # ========================================================

    for result in ranked_results:

        result["score"] = round(
            result["rrf_score"],
            5
        )

        del result["rrf_score"]

    # ========================================================
    # RETURN TOP RESULTS
    # ========================================================

    return ranked_results[:top_k]


# ============================================================
# MAIN RETRIEVAL FUNCTION
# ============================================================

def retrieve_answer_lc(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Hybrid retrieval.

    1. BM25 keyword search
    2. Qdrant semantic search
    3. RRF fusion
    """

    # --------------------------------------------------------
    # STEP 1: Keyword Search
    # --------------------------------------------------------

    keyword_results = _keyword_search(
        query,
        top_k=5,
    )

    # --------------------------------------------------------
    # STEP 2: Semantic Search
    # --------------------------------------------------------

    semantic_results = _semantic_search(
        query,
        top_k=5,
    )

    # --------------------------------------------------------
    # STEP 3: Fuse Both Results
    # --------------------------------------------------------

    results = _rrf_fusion(
        keyword_results,
        semantic_results,
        top_k=top_k,
    )

    return results