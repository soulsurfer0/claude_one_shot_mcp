# MCP RAG Server

A production-style Python RAG (Retrieval-Augmented Generation) backend exposed as a Model Context Protocol (MCP) server.

## What It Is

This system ingests plain-text documents, chunks them deterministically, generates vector embeddings, stores them in PostgreSQL via pgvector, and exposes ingestion and semantic retrieval as MCP tools consumable by any MCP-capable client (Claude Desktop, Cursor, etc.).

## Architecture Overview

```
Plain text document
        │
        ▼
document_registry   ── SHA256 hash → idempotent INSERT into documents
        │
        ▼
    chunker         ── 1000-char chunks, 200-char overlap → INSERT into chunks
        │
        ▼
   BGEEmbedder      ── BAAI/bge-small-en-v1.5 → 384-dim vectors
        │
        ▼
embedding store     ── pgvector INSERT into chunk_embeddings (HNSW index)
        │
        ▼
  retrieval/search  ── cosine similarity top-k via <=> operator
        │
        ▼
  MCP server        ── stdio transport, 3 tools exposed to MCP clients
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full detail.

## Requirements

- Python 3.12
- PostgreSQL 16 with pgvector extension enabled
- pip / venv

## Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/soulsurfer0/claude_one_shot_mcp.git
cd claude_one_shot_mcp
python -m venv .venv
```

Activate:
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

Required variables:

| Variable | Description | Default |
|----------|-------------|---------|
| DB_HOST | PostgreSQL host | localhost |
| DB_PORT | PostgreSQL port | 5432 |
| DB_NAME | Database name | rag_db |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | — |
| EMBEDDING_MODEL | Sentence-transformers model | BAAI/bge-small-en-v1.5 |
| EMBEDDING_DIM | Embedding dimensions | 384 |

### 4. Create database and initialize schema

```bash
# Create the database (as postgres superuser)
psql -U postgres -c "CREATE DATABASE rag_db;"
psql -U postgres -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Initialize tables and indexes
python scripts/init_db.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```

All 45 tests should pass.

## Ingesting a Document

```python
from dotenv import load_dotenv
load_dotenv()
from src.db.connection import get_pool
from src.embeddings.embedder import get_default_embedder
from src.rag_backend import RAGBackend

pool = get_pool()
backend = RAGBackend(pool=pool, embedder=get_default_embedder())

result = backend.ingest_document("path/to/document.txt")
print(result)
# {'document_id': '...', 'chunk_count': 4, 'embedding_count': 4, 'status': 'ingested'}
```

## Performing a Retrieval Query

```python
results = backend.retrieve("how do black holes form", top_k=3)
for r in results:
    print(r['source_name'], r['similarity'], r['content'][:100])
```

## MCP Server Usage

### Starting the server

```bash
python src/server.py
```

The server communicates over stdio using the MCP protocol.

### Claude Desktop configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rag-server": {
      "command": "python",
      "args": ["path/to/claude_one_shot_mcp/src/server.py"],
      "cwd": "path/to/claude_one_shot_mcp"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `ingest_document` | Ingest a .txt or .md file into the RAG system |
| `retrieve_chunks` | Semantic search: retrieve top-k relevant chunks for a query |
| `health_check` | Report DB connectivity and embedding model status |

## Current Project Status

See [PROJECT_STATE.md](PROJECT_STATE.md).
