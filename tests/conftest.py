"""Shared pytest fixtures for the MCP RAG Server test suite."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env before any test runs
load_dotenv(Path(__file__).parent.parent / ".env")

from src.db.connection import get_pool, close_pool
from src.embeddings.embedder import BGEEmbedder


@pytest.fixture(scope="session")
def pool():
    """Session-scoped connection pool."""
    p = get_pool()
    yield p
    close_pool()


@pytest.fixture(scope="session")
def embedder():
    """Session-scoped BGE embedder (downloads model once)."""
    return BGEEmbedder()


@pytest.fixture
def tmp_txt_file(tmp_path):
    """A temporary .txt file with enough content to produce multiple chunks."""
    content = "The quick brown fox jumps over the lazy dog. " * 100
    f = tmp_path / "test_doc.txt"
    f.write_text(content, encoding="utf-8")
    return f


@pytest.fixture
def tmp_short_txt_file(tmp_path):
    """A temporary .txt file with short content (< 1000 chars)."""
    content = "Short document content for testing."
    f = tmp_path / "short_doc.txt"
    f.write_text(content, encoding="utf-8")
    return f
