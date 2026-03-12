# ARCHITECTURE.md

## System Overview

The MCP RAG Server is a Python backend that combines PostgreSQL, pgvector, and sentence-transformers into a pipeline exposed via the Model Context Protocol.

## Database Tables

### documents
Content-addressed document registry. Each unique document (by SHA256 hash of content) occupies exactly one row.

```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
source_path   TEXT NOT NULL               -- resolved absolute path at ingestion time
source_name   TEXT NOT NULL               -- human-readable label
source_type   TEXT NOT NULL               -- text/plain | text/markdown | ...
file_hash     TEXT NOT NULL UNIQUE        -- SHA256 hex; identity key
metadata      JSONB NOT NULL DEFAULT '{}'
created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### chunks
Character-sliced text fragments of documents.

```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE
chunk_index   INTEGER NOT NULL            -- 0-based position within document
content       TEXT NOT NULL               -- exact text slice
char_count    INTEGER NOT NULL            -- = end_offset - start_offset
token_count   INTEGER                     -- NULL in v1
start_offset  INTEGER NOT NULL            -- inclusive
end_offset    INTEGER NOT NULL            -- exclusive
metadata      JSONB NOT NULL DEFAULT '{}'
created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
UNIQUE (document_id, chunk_index)
```

### chunk_embeddings
Vector embeddings for chunks, keyed by (chunk, model).

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
chunk_id        UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE
embedding_model TEXT NOT NULL             -- model identifier string
embedding_dim   INTEGER NOT NULL          -- validated before insert
embedding       VECTOR(384) NOT NULL      -- pgvector type
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
UNIQUE (chunk_id, embedding_model)
```

HNSW index for cosine similarity search:
```sql
CREATE INDEX idx_chunk_embeddings_hnsw
    ON chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

## Pipeline

```
ingest_document(file_path)
    │
    ├─ compute_file_hash(path)          SHA256 via 64 KiB chunked reads
    ├─ register_document(pool, path)    INSERT ... ON CONFLICT DO NOTHING
    ├─ read text                        path.read_text(encoding='utf-8')
    ├─ chunk_text(text, 1000, 200)      deterministic sliding window
    ├─ persist_chunks(pool, ...)        INSERT ... ON CONFLICT DO NOTHING
    ├─ BGEEmbedder.embed(contents)      batch → (N, 384) float32 ndarray
    └─ store_embeddings(pool, ...)      INSERT ... ON CONFLICT DO NOTHING

retrieve(query, top_k)
    │
    ├─ BGEEmbedder.embed_one(query)     query → (384,) float32 ndarray
    └─ SELECT ... ORDER BY embedding <=> query_vec LIMIT top_k
```

## Idempotency Rules

| Layer | Rule |
|-------|------|
| Document | `UNIQUE (file_hash)` — same content, same UUID |
| Chunk | `UNIQUE (document_id, chunk_index)` — re-ingestion skips existing chunks |
| Embedding | `UNIQUE (chunk_id, embedding_model)` — re-embedding is a no-op |

All INSERT statements use `ON CONFLICT DO NOTHING`.

## Embedding Model

**BAAI/bge-small-en-v1.5** via `sentence-transformers`

- Dimensions: 384
- Embeddings are L2-normalized (cosine similarity = dot product)
- Model is loaded once per process (singleton via `get_default_embedder()`)
- Future models can be added by subclassing `Embedder`

## Retrieval Design

Cosine similarity via pgvector's `<=>` operator (cosine distance). Similarity is reported as `1 - distance`, so higher = more relevant. Results are ordered by distance ascending (most similar first).

The HNSW index provides approximate nearest-neighbour search with sub-linear query time at scale.

## MCP Server

The server uses `FastMCP` from the official Python MCP SDK.

- **Transport:** stdio (stdin/stdout)
- **Logging:** stderr only — stdout is reserved for MCP wire protocol
- **Lazy init:** backend and connection pool initialized on first tool call
- **Tools:** `ingest_document`, `retrieve_chunks`, `health_check`

The server is stateless across calls but maintains a persistent connection pool and a loaded embedding model for the lifetime of the process.
