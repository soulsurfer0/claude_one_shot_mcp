# LLM Build Evaluation Rubric

This document defines a structured rubric for evaluating whether an autonomous coding agent successfully implemented the MCP RAG Server specified in `CLAUDE_CODE_MASTER_PROMPT.md`.

The goal is to evaluate both:

1. **Engineering quality** of the produced system
2. **Autonomous capability** of the LLM agent

This rubric is intended to make the experiment measurable rather than subjective.

---

# Evaluation Method

Each category is scored from **0–5**.

Score definitions:

| Score | Meaning |
|------|--------|
| 0 | Not implemented / completely incorrect |
| 1 | Attempted but fundamentally broken |
| 2 | Partially implemented but unreliable |
| 3 | Functional but with notable issues |
| 4 | Correct and reliable implementation |
| 5 | Excellent implementation with strong engineering discipline |

Total possible score depends on the number of sections evaluated.

---

# 1. Planning Quality

Evaluate the quality of `IMPLEMENTATION_PLAN.md`.

Criteria:

- clearly defines project objective
- proposes correct repository structure
- describes database schema correctly
- lists staged implementation order
- describes testing strategy
- includes smoke testing plan
- identifies risks and mitigations

Score guidance:

| Score | Description |
|------|-------------|
| 0 | No plan produced |
| 1 | Plan incomplete or mostly incorrect |
| 3 | Reasonable but missing several elements |
| 4 | Solid engineering plan |
| 5 | Professional-quality design document |

---

# 2. Repository Structure

Evaluate whether the final repository structure follows requirements.

Required rules:

- all functional code under `src/`
- all tests under `tests/`
- logical module separation

Example structure:

```
src/
    db/
    ingestion/
    embeddings/
    retrieval/
    server.py

tests/
```

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Structure completely wrong |
| 2 | Mixed structure with rule violations |
| 3 | Mostly correct |
| 4 | Fully correct |
| 5 | Excellent modular architecture |

---

# 3. Database Design

Evaluate schema correctness.

Tables required:

- documents
- chunks
- chunk_embeddings

Criteria:

- correct primary keys
- correct foreign keys
- uniqueness constraints implemented
- HNSW index created
- pgvector integration correct

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Schema missing or unusable |
| 2 | Tables exist but incorrect constraints |
| 3 | Mostly correct schema |
| 4 | Fully correct schema |
| 5 | Production-quality schema |

---

# 4. Deterministic Ingestion

Evaluate ingestion behavior.

Required properties:

- SHA256 file hashing
- idempotent document registration
- chunk insertion skipping duplicates

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Not implemented |
| 2 | Implemented but non-deterministic |
| 3 | Works but fragile |
| 4 | Deterministic and reliable |
| 5 | Clean implementation with proper safeguards |

---

# 5. Chunking Correctness

Evaluate chunking logic.

Requirements:

- chunk size = 1000
- overlap = 200
- deterministic offsets
- correct start/end offsets
- exact slice preservation

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Incorrect algorithm |
| 2 | Overlap or offsets wrong |
| 3 | Mostly correct |
| 4 | Fully correct |
| 5 | Clean and well-tested implementation |

---

# 6. Embedding Generation

Evaluate embedding pipeline.

Criteria:

- uses `BAAI/bge-small-en-v1.5`
- generates 384-dimensional vectors
- embedding model abstraction present
- batch processing implemented

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Embeddings missing |
| 2 | Embeddings generated incorrectly |
| 3 | Functional but limited |
| 4 | Correct embedding generation |
| 5 | Clean extensible embedder design |

---

# 7. Embedding Storage

Evaluate embedding persistence.

Requirements:

- vectors stored in pgvector
- `(chunk_id, embedding_model)` uniqueness enforced
- idempotent insertion

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Storage missing |
| 2 | Storage unreliable |
| 3 | Functional but incomplete |
| 4 | Correct and idempotent |
| 5 | Production-quality implementation |

---

# 8. Retrieval Quality

Evaluate search behavior.

Criteria:

- query embedding generation
- cosine similarity search
- deterministic top-k retrieval
- relevant chunk returned for known queries

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Retrieval missing |
| 2 | Retrieval returns incorrect results |
| 3 | Works inconsistently |
| 4 | Reliable retrieval |
| 5 | High-quality semantic retrieval |

---

# 9. MCP Server Implementation

Evaluate MCP integration.

Criteria:

- MCP server starts successfully
- ingestion tool exposed
- retrieval tool exposed
- stdio transport preserved

Score guidance:

| Score | Description |
|------|-------------|
| 0 | No server |
| 2 | Server exists but unusable |
| 3 | Basic server working |
| 4 | Fully functional MCP server |
| 5 | Clean tool interface design |

---

# 10. Test Suite Quality

Evaluate test coverage.

Criteria:

- pytest used
- unit tests for major modules
- integration tests exist
- idempotency verified

Score guidance:

| Score | Description |
|------|-------------|
| 0 | No tests |
| 2 | Very limited tests |
| 3 | Basic coverage |
| 4 | Strong coverage |
| 5 | Excellent test discipline |

---

# 11. Autonomous Debugging Capability

Evaluate whether the LLM fixed issues itself.

Evidence:

- ran tests
- fixed failing tests
- reran tests
- repeated until green

Score guidance:

| Score | Description |
|------|-------------|
| 0 | Required human intervention |
| 2 | Partial debugging |
| 3 | Fixed some issues |
| 4 | Autonomous debugging mostly successful |
| 5 | Fully autonomous debugging |

---

# 12. Smoke Test Success

Evaluate real-world functionality.

Required steps:

1. ingest sample documents
2. verify chunks stored
3. verify embeddings stored
4. run retrieval queries
5. verify relevant responses

Score guidance:

| Score | Description |
|------|-------------|
| 0 | System unusable |
| 2 | Partial functionality |
| 3 | Works but unreliable |
| 4 | Reliable end-to-end system |
| 5 | Fully operational RAG backend |

---

# Final Score

Maximum possible score: **60**

Suggested interpretation:

| Score Range | Interpretation |
|-------------|---------------|
| 0–20 | System failed |
| 21–35 | Partial implementation |
| 36–45 | Functional system |
| 46–55 | Strong engineering result |
| 56–60 | Exceptional autonomous build |

---

# Purpose of This Rubric

This rubric ensures the experiment measures:

- engineering correctness
- architectural quality
- autonomous debugging ability
- real-world usefulness

Rather than relying on subjective impressions of the generated code.

