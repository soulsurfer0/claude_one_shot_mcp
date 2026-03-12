"""
MCP RAG Server.

Exposes ingestion, retrieval, and health tools via the Model Context Protocol.
Transport: stdio. All application logging goes to stderr — stdout is reserved
for the MCP protocol wire format.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
# when the server is launched directly (python src/server.py)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
from typing import Any

# Route all logging to stderr so stdout stays clean for MCP protocol
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_server")

from mcp.server.fastmcp import FastMCP

from src.db.connection import get_pool
from src.embeddings.embedder import get_default_embedder
from src.rag_backend import RAGBackend

mcp = FastMCP("rag-server")

# Lazy-initialise backend on first tool call
_backend: RAGBackend | None = None


def _get_backend() -> RAGBackend:
    global _backend
    if _backend is None:
        logger.info("Initialising RAG backend ...")
        pool = get_pool()
        embedder = get_default_embedder()
        _backend = RAGBackend(pool=pool, embedder=embedder)
        logger.info("RAG backend ready.")
    return _backend


@mcp.tool()
def ingest_document(
    file_path: str,
    source_name: str = "",
    metadata: dict = {},
) -> dict:
    """
    Ingest a plain-text (.txt or .md) document into the RAG system.

    Args:
        file_path: Absolute or relative path to the document.
        source_name: Optional human-readable label for the document.
        metadata: Optional arbitrary JSON metadata to attach.

    Returns:
        document_id, chunk_count, embedding_count, status.
    """
    logger.info("ingest_document called: %s", file_path)
    backend = _get_backend()
    return backend.ingest_document(
        file_path=file_path,
        source_name=source_name or None,
        metadata=metadata or None,
    )


@mcp.tool()
def retrieve_chunks(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve the most relevant document chunks for a natural language query.

    Args:
        query: The search query.
        top_k: Number of results to return (default 5).

    Returns:
        List of chunks with content and similarity scores.
    """
    logger.info("retrieve_chunks called: query=%r top_k=%d", query, top_k)
    backend = _get_backend()
    results = backend.retrieve(query, top_k=top_k)
    # Convert similarity to float for JSON serialisation
    for r in results:
        if "similarity" in r:
            r["similarity"] = float(r["similarity"])
    return results


@mcp.tool()
def health_check() -> dict:
    """
    Report the health status of the RAG server.

    Returns:
        status, db_connected, embedding_model, vector_dims.
    """
    logger.info("health_check called")
    backend = _get_backend()
    return backend.health()


if __name__ == "__main__":
    logger.info("Starting MCP RAG server on stdio ...")
    mcp.run(transport="stdio")
