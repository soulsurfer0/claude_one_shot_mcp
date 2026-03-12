"""Tests for embedding storage."""
from __future__ import annotations

import pytest

from src.embeddings.store import store_document_embeddings
from src.ingestion.chunker import ingest_text_document


def test_store_embeddings(pool, embedder, tmp_txt_file):
    """Embeddings are stored in chunk_embeddings table."""
    result = ingest_text_document(pool, tmp_txt_file)
    doc_id = result["document_id"]

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
                (doc_id,),
            )
            rows = cur.fetchall()

    chunk_ids = [str(r[0]) for r in rows]
    contents = [r[1] for r in rows]

    inserted = store_document_embeddings(pool, chunk_ids, contents, embedder)
    assert inserted > 0

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM chunk_embeddings WHERE chunk_id = ANY(%s::uuid[])",
                (chunk_ids,),
            )
            count = cur.fetchone()[0]
    assert count == len(chunk_ids)


def test_idempotent_storage(pool, embedder, tmp_txt_file):
    """Storing embeddings twice does not create duplicates."""
    result = ingest_text_document(pool, tmp_txt_file)
    doc_id = result["document_id"]

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
                (doc_id,),
            )
            rows = cur.fetchall()

    chunk_ids = [str(r[0]) for r in rows]
    contents = [r[1] for r in rows]

    store_document_embeddings(pool, chunk_ids, contents, embedder)
    inserted2 = store_document_embeddings(pool, chunk_ids, contents, embedder)
    assert inserted2 == 0  # No new rows on second run
