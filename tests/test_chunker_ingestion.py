"""Integration tests for chunker ingestion (requires DB)."""
from __future__ import annotations

import pytest

from src.ingestion.chunker import ingest_text_document


def test_end_to_end_ingestion(pool, tmp_txt_file):
    """Ingesting a file creates chunk rows in the database."""
    result = ingest_text_document(pool, tmp_txt_file)
    assert "document_id" in result
    assert "chunk_ids" in result
    assert len(result["chunk_ids"]) > 0

    # Verify chunks exist in DB
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_id = %s",
                (result["document_id"],),
            )
            count = cur.fetchone()[0]
    assert count == len(result["chunk_ids"])


def test_idempotent_ingestion(pool, tmp_txt_file):
    """Ingesting the same file twice does not create duplicate chunks."""
    result1 = ingest_text_document(pool, tmp_txt_file)
    result2 = ingest_text_document(pool, tmp_txt_file)

    assert result1["document_id"] == result2["document_id"]

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM chunks WHERE document_id = %s",
                (result1["document_id"],),
            )
            count = cur.fetchone()[0]
    assert count == len(result1["chunk_ids"])
