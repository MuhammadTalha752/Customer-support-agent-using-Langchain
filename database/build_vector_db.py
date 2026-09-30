"""
LangChain equivalent of knowledge/build_vector_db.py
Run with: python langchain_version/build_vector_db_lc.py
Builds a SEPARATE Qdrant store (data/qdrant_store_langchain/) so it never
conflicts with your existing hand-built version in data/qdrant_store/.
"""
import json
import os
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant_store_langchain")
COLLECTION_NAME = "appinsnap_kb_lc"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def build():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)

    # LangChain's core unit is a "Document" -- page_content is what gets
    # embedded, metadata is extra data carried alongside (not embedded).
    docs = [
        Document(
            page_content=f"{item['topic']}. {item['content']}",
            metadata={ "id": item["id"],"topic": item["topic"], "content": item["content"]},
        )
        for item in kb
    ]

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # One line replaces the manual "encode + upsert" loop we wrote by hand
    # in build_vector_db.py -- LangChain handles embedding + storing together.
    QdrantVectorStore.from_documents(
        docs,
        embeddings,
        path=DB_PATH,
        collection_name=COLLECTION_NAME,
        force_recreate=True,
    )
    print(f"Stored {len(kb)} entries into LangChain-managed Qdrant store at:\n  {DB_PATH}")


if __name__ == "__main__":
    build()