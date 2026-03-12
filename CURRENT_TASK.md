# CURRENT_TASK.md

## Status: Implementation Complete

The MCP RAG Server is fully built, tested, and operational.

## Next Milestones (Post-Experiment)

The following improvements could be made in future iterations:

1. **Multi-model support** — Add additional embedding models (e.g., OpenAI text-embedding-3-small) via the existing `Embedder` interface.

2. **Async ingestion pipeline** — Replace synchronous embedding generation with async batch processing for large document sets.

3. **Document update support** — Currently, documents are immutable (content-addressed). Add support for updating metadata or re-indexing with a new model.

4. **Chunk metadata enrichment** — Add section headings, page numbers, or other structural metadata during chunking.

5. **REST API layer** — Wrap the RAG backend in a FastAPI server as an alternative to MCP transport.

6. **Docker Compose setup** — Add a `docker-compose.yml` for one-command local development with PostgreSQL + pgvector pre-configured.

7. **CI/CD pipeline** — Add GitHub Actions workflow to run the test suite on push.

## Experiment Evaluation

This build is ready for scoring against `llm_build_eval_rubric.md`.
