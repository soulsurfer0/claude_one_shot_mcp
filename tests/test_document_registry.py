"""Tests for the document registry module."""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from src.ingestion.document_registry import (
    compute_file_hash,
    infer_source_type,
    register_document,
)


def test_sha256_hash(tmp_path):
    """SHA256 hash of known content matches expected value."""
    content = b"hello world"
    f = tmp_path / "test.txt"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert compute_file_hash(f) == expected


def test_sha256_hash_deterministic(tmp_path):
    """Same content always produces same hash."""
    content = "deterministic content " * 100
    f = tmp_path / "det.txt"
    f.write_text(content, encoding="utf-8")
    h1 = compute_file_hash(f)
    h2 = compute_file_hash(f)
    assert h1 == h2


def test_path_normalization(pool, tmp_txt_file):
    """register_document resolves relative paths without error."""
    doc_id, is_new = register_document(pool, tmp_txt_file)
    assert doc_id is not None
    assert len(doc_id) == 36  # UUID format


def test_source_type_txt():
    assert infer_source_type(Path("file.txt")) == "text/plain"


def test_source_type_md():
    assert infer_source_type(Path("file.md")) == "text/markdown"


def test_source_type_unknown():
    assert infer_source_type(Path("file.pdf")) == "application/octet-stream"


def test_idempotent_registration(pool, tmp_path):
    """Registering the same file twice returns the same document_id."""
    # UUID suffix guarantees a fresh hash each run — no cross-run contamination
    content = f"unique idempotency test content {uuid.uuid4()}"
    f = tmp_path / "idem.txt"
    f.write_text(content, encoding="utf-8")

    id1, new1 = register_document(pool, f)
    id2, new2 = register_document(pool, f)

    assert id1 == id2
    assert new1 is True
    assert new2 is False


def test_file_not_found(pool):
    """FileNotFoundError raised for missing files."""
    with pytest.raises(FileNotFoundError):
        register_document(pool, "/nonexistent/path/file.txt")
