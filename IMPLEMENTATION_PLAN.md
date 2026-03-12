# IMPLEMENTATION_PLAN.md

## MCP RAG Server — Engineering Plan

**Status:** Awaiting approval before implementation begins.

---

## 1. Project Objective

Build a production-style Python RAG (Retrieval-Augmented Generation) backend exposed as a Model Context Protocol (MCP) server.

The system will:

- Accept plain-text documents (`.txt`, `.md`) for ingestion
- Hash and register documents deterministically in PostgreSQL
- Chunk documents with fixed overlap
- Generate 384-dimensional embeddings using `BAAI/bge-small-en-v1.5`
- Store vectors in PostgreSQL via the `pgvector` extension
- Expose ingestion, retrieval, and health tools over MCP stdio transport
- Be fully tested and ready to use

---

## 2. Repository Structure

```
claude_one_shot_mcp/
├── src/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── connection.py          # psycopg3 connection pool, env validation
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── document_registry.py   # SHA256 hashing, idempotent doc registration
│   │   └── chunker.py             # Character-based chunking + DB persistence
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── embedder.py            # Embedder interface + BGE model wrapper
│   │   └── store.py               # Idempotent vector storage via pgvector
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── search.py              # Cosine similarity retrieval, top-k
│   ├── rag_backend.py             # High-level façade: ingest + retrieve
│   └── server.py                  # MCP server with tool definitions
├── tests/
│   ├── conftest.py                # Shared fixtures: DB pool, sample files
│   ├── test_db_connection.py
│   ├── test_document_registry.py
│   ├── test_chunker.py
│   ├── test_chunker_ingestion.py
│   ├── test_embedder.py
│   ├── test_embedding_store.py
│   ├── test_retrieval.py
│   └── test_server_tools.py
├── schema/
│   └── init.sql                   # DDL for all tables + indexes
├── scripts/
│   └── init_db.py                 # Runs init.sql against configured DB
├── sample_docs/                   # Sample text files for smoke testing
│   ├── astronomy.txt
│   ├── cooking.txt
│   └── software_engineering.txt
├── IMPLEMENTATION_PLAN.md         # This file
├── README.md
├── ARCHITECTURE.md
├── PROJECT_STATE.md
├── CURRENT_TASK.md
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 3. Database Schema Summary

### Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Table: `documents`

Stores one row per unique document (content-addressable by SHA256 hash).

| Column        | Type                           | Notes                    |
|---------------|--------------------------------|--------------------------|
| id            | UUID PRIMARY KEY               | gen_random_uuid()        |
| source_path   | TEXT NOT NULL                  | Absolute resolved path   |
| source_name   | TEXT NOT NULL                  | Human-readable name      |
| source_type   | TEXT NOT NULL                  | e.g. "text/plain"        |
| file_hash     | TEXT NOT NULL UNIQUE           | SHA256 hex of content    |
| metadata      | JSONB NOT NULL DEFAULT '{}'    |                          |
| created_at    | TIMESTAMPTZ NOT NULL DEFAULT NOW() |                     |
| updated_at    | TIMESTAMPTZ NOT NULL DEFAULT NOW() |                     |

Constraint: `UNIQUE (file_hash)` — prevents duplicate document registration.

### Table: `chunks`

Stores character-sliced text chunks derived from a document.

| Column       | Type                               | Notes                      |
|--------------|------------------------------------|----------------------------|
| id           | UUID PRIMARY KEY                   | gen_random_uuid()          |
| document_id  | UUID NOT NULL REFERENCES documents ON DELETE CASCADE | |
| chunk_index  | INTEGER NOT NULL                   | 0-based                    |
| content      | TEXT NOT NULL                      | Exact text slice           |
| char_count   | INTEGER NOT NULL                   | end_offset - start_offset  |
| token_count  | INTEGER NULL                       | Optional, not computed v1  |
| start_offset | INTEGER NOT NULL                   | Inclusive                  |
| end_offset   | INTEGER NOT NULL                   | Exclusive                  |
| metadata     | JSONB NOT NULL DEFAULT '{}'        |                            |
| created_at   | TIMESTAMPTZ NOT NULL DEFAULT NOW() |                            |

Constraint: `UNIQUE (document_id, chunk_index)` — prevents duplicate chunks.

### Table: `chunk_embeddings`

Stores embedding vectors for each chunk, keyed by model.

| Column          | Type                               | Notes                   |
|-----------------|------------------------------------|-------------------------|
| id              | UUID PRIMARY KEY                   | gen_random_uuid()       |
| chunk_id        | UUID NOT NULL REFERENCES chunks ON DELETE CASCADE | |
| embedding_model | TEXT NOT NULL                      | Model identifier string |
| embedding_dim   | INTEGER NOT NULL                   | Validated before insert |
| embedding       | VECTOR(384) NOT NULL               | pgvector type           |
| created_at      | TIMESTAMPTZ NOT NULL DEFAULT NOW() |                         |

Constraint: `UNIQUE (chunk_id, embedding_model)` — idempotent embedding storage.

Index: `HNSW` on `embedding` using `vector_cosine_ops` for fast similarity search.

---

## 4. Implementation Stages (Dependency Order)

| Stage | Description | Depends On |
|-------|-------------|------------|
| 1 | Project scaffolding — dirs, `.gitignore`, `.env.example`, `requirements.txt` | Nothing |
| 2 | `schema/init.sql` — DDL for all 3 tables + HNSW index | Nothing |
| 3 | `scripts/init_db.py` — run schema against configured DB | Stage 2 |
| 4 | `src/db/connection.py` — env validation, psycopg3 pool | Stage 1 |
| 5 | `src/ingestion/document_registry.py` — SHA256, path normalization, idempotent insert | Stage 4 |
| 6 | `src/ingestion/chunker.py` — character chunking + DB persistence | Stage 5 |
| 7 | `src/embeddings/embedder.py` — model-agnostic interface + BGE wrapper | Stage 4 |
| 8 | `src/embeddings/store.py` — idempotent vector insert via pgvector | Stage 7 |
| 9 | `src/retrieval/search.py` — cosine similarity top-k retrieval | Stage 8 |
| 10 | `src/rag_backend.py` — end-to-end ingest + retrieve façade | Stage 6, 8, 9 |
| 11 | `src/server.py` — MCP server with 3 tools | Stage 10 |
| 12 | `tests/` — full pytest suite with fixtures | All stages |
| 13 | `sample_docs/` + smoke test execution | Stage 11 |
| 14 | Docs: README, ARCHITECTURE, PROJECT_STATE, CURRENT_TASK | Stage 13 |

At each stage, relevant tests will be written and run before advancing.

---

## 5. Testing Strategy

**Framework:** `pytest`

**Approach:**

- `tests/conftest.py` provides a real DB connection pool fixture scoped to the test session. Tests run against a real PostgreSQL instance. A test database name can be configured via `.env`.
- Each test module maps to a `src/` module.
- Fixtures create and clean up test data (unique hashes, temp files) to keep tests isolated.
- No mocking of DB — tests verify real SQL behavior.
- Embedder tests verify shape (384-dim) without requiring a specific numeric value.
- Retrieval tests ingest known documents then assert that a semantically relevant query returns the expected chunk.

**Coverage per module:**

| Module | Key Tests |
|--------|-----------|
| db/connection | Pool init, acquire connection, execute SQL |
| ingestion/document_registry | SHA256 correctness, path normalization, source_type inference, idempotency (same file twice = same UUID) |
| ingestion/chunker | Empty input, whitespace-only, short text (<1000 chars), overlap correctness (200 char), offset math, exact slice preservation, invalid params, end-to-end idempotency |
| embeddings/embedder | Returns ndarray of shape (384,), batch mode works |
| embeddings/store | Inserts correctly, second insert on same (chunk_id, model) is a no-op |
| retrieval/search | Known query retrieves expected chunk, top-k respected, ordering deterministic |
| server (MCP tools) | Tool handlers are callable and return expected shape |

---

## 6. Smoke Test Strategy

After full implementation and test suite pass, manually execute:

1. Create `sample_docs/astronomy.txt`, `sample_docs/cooking.txt`, `sample_docs/software_engineering.txt` with distinct, semantically meaningful content (~2000 chars each to produce multiple chunks).
2. Run ingestion for all three documents via `rag_backend.ingest_document()`.
3. `SELECT COUNT(*) FROM documents` → expect 3.
4. `SELECT COUNT(*) FROM chunks` → expect > 3 (multiple chunks per doc).
5. `SELECT COUNT(*) FROM chunk_embeddings` → same count as chunks.
6. Run retrieval queries:
   - `"How do black holes form?"` → expect astronomy chunk in top result
   - `"How do I make pasta?"` → expect cooking chunk in top result
   - `"What is a design pattern?"` → expect software engineering chunk
7. Verify MCP server starts (`python src/server.py`) and reports tools via MCP handshake.

If any step fails, fix and rerun.

---

## 7. MCP Server Design Summary

**Transport:** stdio (stdin/stdout) — no HTTP/WebSocket.

**SDK:** Official Python MCP SDK (`mcp` package).

**Logging:** All log output directed to `stderr` only. stdout is reserved for MCP protocol messages.

**Tools exposed:**

### `ingest_document`
```
Input:
  file_path: str        — absolute or relative path to .txt or .md file
  source_name: str?     — human label (defaults to filename)
  metadata: object?     — arbitrary JSON metadata

Output:
  document_id: str      — UUID of registered document
  chunk_count: int      — number of chunks created
  embedding_count: int  — number of embeddings stored
  status: str           — "ingested" | "already_exists"
```

### `retrieve_chunks`
```
Input:
  query: str            — natural language query
  top_k: int?           — number of results (default 5)
  embedding_model: str? — model identifier (default BAAI/bge-small-en-v1.5)

Output:
  results: list of {
    chunk_id: str
    document_id: str
    source_name: str
    chunk_index: int
    content: str
    similarity: float
  }
```

### `health_check`
```
Input: none

Output:
  status: str           — "ok" | "degraded"
  db_connected: bool
  embedding_model: str
  vector_dims: int
```

**Server entry point:** `python src/server.py`

---

## 8. Expected Dependencies

```
# Database
psycopg[binary]>=3.1.0
psycopg-pool>=3.1.0
pgvector>=0.3.0

# Embeddings
sentence-transformers>=2.7.0

# MCP
mcp>=1.0.0

# Config
python-dotenv>=1.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0

# Utilities (likely transitive but pinned for reproducibility)
numpy>=1.24.0
```

Exact versions will be captured after successful install via `pip freeze`.

---

## 9. Key Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `pgvector` extension not enabled | Medium | Schema init script checks; clear error message on failure |
| `sentence-transformers` first model download slow | High | Document in README; model cached to `~/.cache/` after first run |
| MCP SDK API changes | Low | Pin version; test tool registration before full implementation |
| Windows vs Linux path separator differences | Medium | Use `pathlib.Path` throughout; normalize to POSIX for DB storage |
| psycopg3 vs psycopg2 API confusion | Medium | Use `psycopg` (v3) exclusively; document in README |
| HNSW index build time on large datasets | Low | Not a concern for development / test scale |
| Test DB collisions between parallel runs | Low | Use unique hashes and UUIDs in fixtures; teardown in conftest |
| MCP stdio corruption via logging | Medium | Route all logging to `stderr`; validate by running server and inspecting stdout |

---

## 10. Acceptance Criteria Checklist

- [ ] `IMPLEMENTATION_PLAN.md` was created before any implementation code
- [ ] User explicitly approved this plan before implementation began
- [ ] Repository structure matches the required layout (`src/`, `tests/`)
- [ ] `requirements.txt` installs cleanly via `pip install -r requirements.txt`
- [ ] PostgreSQL + pgvector connection works via `.env` configuration
- [ ] `.txt` and `.md` documents can be ingested end-to-end
- [ ] Chunks are persisted with correct offsets and idempotency
- [ ] Embeddings (384-dim) are generated and stored in pgvector
- [ ] Retrieval returns semantically relevant chunks for natural language queries
- [ ] MCP server starts via `python src/server.py` and exposes all 3 tools
- [ ] Full `pytest` suite passes (0 failures, 0 errors)
- [ ] Smoke tests pass on 3 sample documents with verified retrieval relevance
- [ ] `README.md`, `ARCHITECTURE.md`, `PROJECT_STATE.md`, `CURRENT_TASK.md` reflect final state

---

*Plan complete. Awaiting explicit user approval before implementation begins.*
