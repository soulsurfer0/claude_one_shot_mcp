"""
RAG backend facade.

Provides a high-level interface combining ingestion, embedding, and retrieval.
This is the primary entry point for application code and the MCP server.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from psycopg_pool import ConnectionPool

from src.embeddings.embedder import Embedder, get_default_embedder
from src.embeddings.store import store_document_embeddings
from src.ingestion.chunker import ingest_text_document
from src.retrieval.search import search


class RAGBackend:
    """High-level facade for the RAG pipeline."""

    def __init__(
        self,
        pool: ConnectionPool,
        embedder: Embedder | None = None,
    ) -> None:
        self._pool = pool
        self._embedder = embedder or get_default_embedder()

    def ingest_document(
        self,
        file_path: str | Path,
        source_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        """
        Ingest a document end-to-end: register, chunk, embed, store.

        Returns:
            dict with document_id, chunk_count, embedding_count, status.
        """
        result = ingest_text_document(
            self._pool, file_path, source_name, metadata
        )
        document_id = result["document_id"]
        chunk_ids = result["chunk_ids"]
        is_new = result["is_new"]

        # Fetch chunk contents for embedding
        if chunk_ids:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
                        (document_id,),
                    )
                    rows = cur.fetchall()
            ordered_ids = [str(r[0]) for r in rows]
            ordered_contents = [r[1] for r in rows]
            embedding_count = store_document_embeddings(
                self._pool, ordered_ids, ordered_contents, self._embedder
            )
        else:
            embedding_count = 0

        return {
            "document_id": document_id,
            "chunk_count": len(chunk_ids),
            "embedding_count": embedding_count,
            "status": "ingested" if is_new else "already_exists",
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve top-k chunks most relevant to the query.

        Returns list of result dicts (chunk_id, document_id, source_name,
        chunk_index, content, similarity).
        """
        return search(self._pool, query, self._embedder, top_k=top_k)

    def health(self) -> dict:
        """Return a health/status report."""
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            db_connected = True
        except Exception:
            db_connected = False

        return {
            "status": "ok" if db_connected else "degraded",
            "db_connected": db_connected,
            "embedding_model": self._embedder.model_name,
            "vector_dims": self._embedder.dim,
        }
