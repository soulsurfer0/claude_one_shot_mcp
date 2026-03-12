"""Tests for semantic retrieval."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.rag_backend import RAGBackend
from src.retrieval.search import search


@pytest.fixture(scope="module")
def backend_with_docs(pool, embedder):
    """Backend pre-loaded with sample documents."""
    backend = RAGBackend(pool=pool, embedder=embedder)
    sample_dir = Path(__file__).parent.parent / "sample_docs"
    for doc in sample_dir.glob("*.txt"):
        backend.ingest_document(doc)
    return backend


def test_known_query_retrieves_relevant_chunk(backend_with_docs, pool, embedder):
    """Querying 'black holes' returns astronomy content."""
    results = search(pool, "how do black holes form", embedder, top_k=3)
    assert len(results) > 0
    top_content = results[0]["content"].lower()
    assert any(
        kw in top_content
        for kw in ("black hole", "star", "gravity", "supernova", "neutron")
    )


def test_cooking_query(backend_with_docs, pool, embedder):
    """Querying about pasta returns cooking content."""
    results = search(pool, "how to make pasta dough", embedder, top_k=3)
    assert len(results) > 0
    top_content = results[0]["content"].lower()
    assert any(kw in top_content for kw in ("pasta", "flour", "dough", "cook", "sauce"))


def test_software_query(backend_with_docs, pool, embedder):
    """Querying about design patterns returns software engineering content."""
    results = search(pool, "what is a design pattern in programming", embedder, top_k=3)
    assert len(results) > 0
    top_content = results[0]["content"].lower()
    assert any(kw in top_content for kw in ("pattern", "class", "code", "software", "solid"))


def test_top_k_respected(backend_with_docs, pool, embedder):
    """top_k parameter limits result count."""
    results = search(pool, "test query", embedder, top_k=2)
    assert len(results) <= 2


def test_result_fields(backend_with_docs, pool, embedder):
    """Each result contains all expected fields."""
    results = search(pool, "science and technology", embedder, top_k=1)
    assert len(results) > 0
    r = results[0]
    for field in ("chunk_id", "document_id", "source_name", "chunk_index", "content", "similarity"):
        assert field in r


def test_similarity_range(backend_with_docs, pool, embedder):
    """Similarity scores are in [0, 1] range."""
    results = search(pool, "the universe and stars", embedder, top_k=5)
    for r in results:
        assert 0.0 <= float(r["similarity"]) <= 1.0 + 1e-6
