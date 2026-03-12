# Claude Code Master Prompt — Plan First, Await Approval, Then Build MCP RAG Server

You are an autonomous senior software engineer operating inside Claude Code with full repository access, terminal access, and permission to read/write files, install dependencies, run tests, initialize the database, and iterate on the implementation.

Your task is to build, start-to-finish, a complete, production-style **Python RAG backend exposed as an MCP server**.

However, you must follow a strict two-phase workflow:

1. **Planning phase**
2. **Implementation phase after explicit user approval**

You must not begin implementation until the user has approved the plan.

---

# Operating Mode

You must behave like a disciplined senior engineer.

Required behavior:

- reason carefully before coding
- create a written engineering plan before implementation
- save the plan as a real repository file so it can be downloaded and reviewed
- stop after producing the plan and wait for approval
- after approval, implement the system end to end
- run commands yourself
- run tests yourself
- fix failures yourself
- iterate until acceptance criteria are satisfied
- update documentation to match the final system state

Do not ask broad open-ended questions if the specification is sufficient. Use best engineering judgment within the constraints below.

---

# Phase 1 — Planning Requirements

Before writing implementation code, you must create a plan document in the repository root:

```text
IMPLEMENTATION_PLAN.md
```

The plan must be written for human review and must include at minimum:

1. project objective
2. repository structure to be created
3. database schema summary
4. implementation stages in dependency order
5. testing strategy
6. smoke test strategy
7. MCP server design summary
8. expected dependencies
9. key risks and mitigations
10. acceptance criteria checklist

After creating `IMPLEMENTATION_PLAN.md`, stop and tell the user exactly that the plan is ready for review and approval.

Do not proceed beyond the planning phase until the user explicitly approves the plan.

---

# Phase 2 — Implementation Requirements

After explicit approval, build the entire system without further guidance unless blocked by a truly unrecoverable external issue.

You must continue working until the repository contains a ready-to-run, tested implementation satisfying all requirements below.

---

# Objective

Build a reusable **MCP RAG Server** that:

1. ingests plain-text documents
2. registers documents deterministically in PostgreSQL
3. chunks documents deterministically
4. generates embeddings for chunks
5. stores vectors in pgvector
6. performs semantic retrieval
7. exposes ingestion and retrieval functionality through an MCP server
8. passes all tests
9. includes complete project documentation

The final deliverable must be a ready-to-use repository.

---

# Platform Assumptions

The implementation must be platform-agnostic for development and testing on both **Windows** and **Linux**.

Assume:

- Python 3.12
- PostgreSQL 16
- pgvector PostgreSQL extension enabled
- local development using `.env`
- repository root is the project root

Avoid OS-specific behavior unless guarded carefully.

---

# Required Project Structure

All functional code must live under:

```text
src/
```

All tests must live under:

```text
tests/
```

Expected structure at minimum:

```text
src/
    db/
        connection.py
    ingestion/
        document_registry.py
        chunker.py
    embeddings/
        embedder.py
        store.py
    retrieval/
        search.py
    server.py
    rag_backend.py

tests/
    test_db_connection.py
    test_document_registry.py
    test_chunker.py
    test_chunker_ingestion.py
    test_embedder.py
    test_embedding_store.py
    test_retrieval.py
    test_server_tools.py
```

You may add additional modules if justified, but all code must remain under `src/` and all tests under `tests/`.

---

# Required Documents

The repository must include and keep synchronized:

- `README.md`
- `ARCHITECTURE.md`
- `PROJECT_STATE.md`
- `CURRENT_TASK.md`
- `IMPLEMENTATION_PLAN.md`

These documents must reflect the actual final implementation.

---

# Engineering Requirements

## Deterministic and Idempotent Design

Prefer deterministic systems.

The system must prioritize:

- reproducibility
- explicit database constraints
- idempotent ingestion
- predictable outputs
- clean module boundaries

Idempotency rules:

- duplicate document content must not create a second logical document
- duplicate chunk ingestion for the same document must be skipped
- duplicate embeddings for the same `(chunk_id, embedding_model)` must be skipped

---

# Database Requirements

Use PostgreSQL + pgvector.

Required tables:

## documents

Must contain at least:

- `id UUID PRIMARY KEY`
- `source_path TEXT NOT NULL`
- `source_name TEXT NOT NULL`
- `source_type TEXT NOT NULL`
- `file_hash TEXT NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- timestamps

Required uniqueness:

```sql
UNIQUE (file_hash)
```

## chunks

Must contain at least:

- `id UUID PRIMARY KEY`
- `document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE`
- `chunk_index INTEGER NOT NULL`
- `content TEXT NOT NULL`
- `char_count INTEGER NOT NULL`
- `token_count INTEGER NULL`
- `start_offset INTEGER NOT NULL`
- `end_offset INTEGER NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- timestamps

Required uniqueness:

```sql
UNIQUE (document_id, chunk_index)
```

## chunk_embeddings

Must contain at least:

- `id UUID PRIMARY KEY`
- `chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE`
- `embedding_model TEXT NOT NULL`
- `embedding_dim INTEGER NOT NULL`
- `embedding VECTOR(384) NOT NULL`
- timestamp

Required uniqueness:

```sql
UNIQUE (chunk_id, embedding_model)
```

Create an HNSW cosine index on embeddings.

---

# Database Connection Layer

Implement a database module using:

- `psycopg` (psycopg3)
- `psycopg_pool`
- `.env` for configuration

The connection layer must:

- validate required env vars
- expose pooled connections
- support SQL execution
- be testable

---

# Document Registry Requirements

Implement:

```text
src/ingestion/document_registry.py
```

Required behavior:

- compute SHA256 file hash using chunked file reads
- normalize paths to absolute resolved paths
- infer `source_type` from extension if omitted
- insert document metadata
- return existing `document_id` if file content already exists
- raise `FileNotFoundError` for missing files
- allow DB exceptions to propagate

Document identity must be content-based.

---

# Chunking Requirements

Implement:

```text
src/ingestion/chunker.py
```

Chunking v1 must be:

- character-based
- chunk size = `1000`
- overlap = `200`
- fixed overlap
- deterministic

Offset rules:

- `start_offset` inclusive
- `end_offset` exclusive
- `char_count = end_offset - start_offset`

Behavior rules:

- empty or whitespace-only text → no chunks
- text shorter than chunk size → one chunk
- preserve exact text slices, do not trim chunk content
- `.txt` and `.md` only in v1

Persistence requirements:

- insert chunks into `chunks`
- skip duplicate chunk insertion for documents already chunked

Provide an end-to-end ingestion function for text documents.

---

# Embedding Requirements

Implement:

```text
src/embeddings/embedder.py
src/embeddings/store.py
```

Embedding model:

```text
BAAI/bge-small-en-v1.5
```

Library:

```text
sentence-transformers
```

Execution mode:

- synchronous during ingestion / pipeline execution

Design requirements:

- expose a model-agnostic embedder interface
- generate 384-dimensional embeddings
- validate dimensions before storage
- support batch embedding generation
- skip existing embeddings for the same `(chunk_id, embedding_model)` pair
- allow multiple models in the future

Use `pgvector` Python integration for vector insertion.

---

# Retrieval Requirements

Implement:

```text
src/retrieval/search.py
```

The retrieval layer must:

1. accept a query string
2. generate a query embedding using the same embedding model
3. perform vector similarity search using pgvector cosine distance
4. return top-k relevant chunks
5. include chunk text and relevance information

Requirements:

- configurable `top_k`
- deterministic ordering
- model-aware retrieval
- retrieval tests verifying relevant matches on known inputs

---

# MCP Server Requirements

Implement a real MCP server using the official Python MCP SDK.

The MCP server must expose tools for at least:

1. ingesting a plain-text document
2. retrieving relevant chunks for a query
3. reporting system status / health

The server must be runnable locally over stdio.

Critical requirement:

- never write logging to stdout in a way that corrupts MCP stdio transport
- use stderr or logging appropriately

The MCP server must be usable by MCP-capable clients after setup.

---

# Testing Requirements

Use `pytest`.

The repository is not complete until tests exist and pass.

Required test categories:

## Database

- connection pool initialization
- connection acquisition
- SQL execution

## Document Registry

- deterministic SHA256 hashing
- path normalization
- source type inference
- idempotent document registration

## Chunking

- empty input
- whitespace-only input
- short input
- overlap correctness
- exact offsets
- exact text slice preservation
- invalid parameter handling
- end-to-end ingestion idempotency

## Embeddings

- embedding generation returns 384 dims
- embedding persistence works
- embedding insertion is idempotent

## Retrieval

- known query retrieves relevant chunk(s)
- top-k behavior works
- query embedding path works

## MCP Server

- tool handlers are callable
- ingestion and retrieval tools work through the server abstraction

You must run the full suite repeatedly and keep fixing failures until all tests pass.

---

# Smoke Test Requirements

In addition to the formal test suite, you must run end-to-end smoke tests yourself.

At minimum, after implementation you must:

1. create multiple sample text documents with distinct but meaningfully retrievable content
2. ingest those documents through the implemented ingestion path
3. verify chunk rows exist
4. verify embedding rows exist
5. run retrieval queries against the indexed data
6. verify that the returned results are useful and relevant to the query intent
7. validate MCP server startup and tool availability

If smoke tests reveal a defect, fix the defect and rerun verification.

Do not declare completion until smoke tests succeed.

---

# Reliability and Self-Verification Requirements

You must not stop after code generation.

You must self-verify the repository by running, at minimum:

1. dependency installation
2. test suite
3. document ingestion smoke test
4. embedding generation smoke test
5. retrieval smoke test
6. MCP server startup validation

If any of these fail, fix the problem and rerun until successful.

Use shell access and available tools to iterate autonomously.

Do not declare success unless the product works end to end.

---

# Code Quality Requirements

All code must follow these standards:

- Pythonic, readable, maintainable code
- explicit typing where useful
- minimal hidden coupling
- no imports inside functions unless necessary
- no superficial hack fixes
- no weakening tests to force green status
- avoid unnecessary abstractions
- prioritize correctness over cleverness

When tradeoffs exist, prefer this order:

1. correctness
2. determinism
3. maintainability
4. clarity
5. performance

---

# Dependency Requirements

Create a complete `requirements.txt`.

Expected dependencies will likely include at least:

- psycopg
- psycopg_pool
- pgvector
- python-dotenv
- sentence-transformers
- pytest
- official MCP Python SDK

Do not guess blindly if package names differ; verify them through package installation and successful imports.

---

# Documentation Requirements

`README.md` must explain:

- what the project is
- architecture overview
- setup
- database requirements
- test execution
- ingestion usage
- retrieval usage
- MCP server usage
- current project status

`ARCHITECTURE.md` must describe:

- tables
- pipeline
- idempotency rules
- embedding model choice
- retrieval design
- MCP server role

`PROJECT_STATE.md` must reflect the actual final milestone state.

`CURRENT_TASK.md` must reflect the next milestone after the implementation is complete.

---

# Implementation Strategy Constraints

After approval of the plan, you may plan internally however you want, but the final repository must reflect a clean staged architecture.

Strongly preferred execution pattern:

1. create or verify project structure
2. implement database connection layer
3. implement schema or setup SQL
4. implement document registry
5. implement chunker
6. implement embedding generator
7. implement embedding storage
8. implement retrieval layer
9. implement MCP server
10. write or complete tests
11. update docs
12. run full self-verification

At each major stage, run relevant tests before continuing.

---

# Acceptance Criteria

The task is complete only when all of the following are true:

1. `IMPLEMENTATION_PLAN.md` was created first and approved before coding
2. repository structure matches requirements
3. dependencies install successfully
4. PostgreSQL + pgvector integration works
5. documents can be ingested from `.txt` and `.md`
6. chunks are persisted deterministically
7. embeddings are generated and stored
8. retrieval returns useful results on sample data
9. MCP server starts successfully
10. full pytest suite passes
11. smoke tests pass
12. documentation reflects the final state

If any acceptance criterion is not met, continue working.

---

# Final Output Requirements

When implementation is complete, provide a concise completion summary that includes:

- what was built
- how to run tests
- how to run the server
- how to ingest a document
- how to perform a retrieval query
- required environment variables
- a brief smoke test summary

Remember: first create `IMPLEMENTATION_PLAN.md`, then stop and wait for approval.

