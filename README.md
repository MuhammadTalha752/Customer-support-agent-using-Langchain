# Customer Support Agent using LangChain

An AI-powered customer support agent built with LangChain that combines LLM-based reasoning, hybrid search, knowledge-base retrieval, and database operations to handle customer support queries.

## Pipeline

```text
User Query
     ↓
Intent Detection
     ↓
Query Processing
     ↓
Knowledge Base / Database Retrieval
     ↓
Hybrid Search
(Semantic + Keyword)
     ↓
LLM Reasoning
     ↓
Context-Aware Response
```

## Features

* AI-powered customer support
* Intent detection
* Knowledge-base question answering
* Customer information retrieval
* Complaint registration
* Complaint status checking
* Customer complaint history
* Hybrid semantic + keyword search
* RAG-based knowledge retrieval
* SQLite database integration
* Persistent conversation sessions using user IDs
* Context-aware responses across multiple queries
* Handles unknown or unsupported queries

## Supported Operations

* Register a complaint
* Check complaint status
* View customer complaints
* Answer knowledge-base questions
* Retrieve customer information
* Maintain conversation context
* Handle unknown queries

## Hybrid Search

The agent uses a hybrid retrieval approach that combines:

* **Semantic Search** using Qdrant and Sentence Transformers
* **Keyword Search** using BM25
* **Reciprocal Rank Fusion (RRF)** to combine retrieval results

This approach helps retrieve relevant information using both meaning-based and keyword-based matching.

## Conversation Sessions

The agent maintains separate conversation sessions using a **user ID**.

This allows the system to:

* Maintain conversation history
* Preserve context across multiple queries
* Keep sessions separate for different users
* Generate more context-aware responses

## Technologies

* Python
* LangChain
* Large Language Model (LLM)
* Qdrant
* Sentence Transformers
* BM25
* SQLite
* RAG
* Reciprocal Rank Fusion (RRF)

## Project Structure

```text
├── data/
├── knowledge_base/
├── database/
├── agent/
├── main.py
├── requirements.txt
└── README.md
```

Database files, vector-store data, environment variables, and generated files are excluded from the repository.

## Author

**Muhammad Talha**

BS Computer Science | AI/ML
