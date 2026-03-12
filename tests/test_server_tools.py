"""Tests for MCP server tool handlers via RAGBackend."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.rag_backend import RAGBackend


@pytest.fixture(scope="module")
def backend(pool, embedder):
    return RAGBackend(pool=pool, embedder=embedder)


def test_ingest_tool_callable(backend, tmp_txt_file):
    """ingest_document returns expected fields."""
    result = backend.ingest_document(tmp_txt_file)
    assert "document_id" in result
    assert "chunk_count" in result
    assert "embedding_count" in result
    assert "status" in result
    assert result["status"] in ("ingested", "already_exists")
    assert result["chunk_count"] >= 1


def test_retrieve_tool_callable(backend, tmp_txt_file):
    """retrieve returns a list of result dicts."""
    # Ensure doc is ingested
    backend.ingest_document(tmp_txt_file)
    results = backend.retrieve("fox jumps over dog", top_k=3)
    assert isinstance(results, list)
    if results:
        assert "content" in results[0]
        assert "similarity" in results[0]


def test_health_tool_callable(backend):
    """health() returns expected shape."""
    h = backend.health()
    assert "status" in h
    assert "db_connected" in h
    assert "embedding_model" in h
    assert "vector_dims" in h
    assert h["db_connected"] is True
    assert h["status"] == "ok"
    assert h["vector_dims"] == 384
