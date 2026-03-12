"""
Character-based text chunker.

Splits text into overlapping fixed-size chunks and persists them to PostgreSQL.
Chunking is deterministic: same text always produces same chunks.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from psycopg_pool import ConnectionPool

from src.ingestion.document_registry import register_document

CHUNK_SIZE = 1000
OVERLAP = 200


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[dict]:
    """
    Split text into overlapping character-based chunks.

    Args:
        text: Input text.
        chunk_size: Maximum characters per chunk.
        overlap: Overlap in characters between consecutive chunks.

    Returns:
        List of dicts with keys: chunk_index, content, start_offset,
        end_offset, char_count.

    Raises:
        ValueError: if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be >= 0, got {overlap}")
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be < chunk_size ({chunk_size})")

    if not text or not text.strip():
        return []

    chunks = []
    step = chunk_size - overlap
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        content = text[start:end]
        chunks.append({
            "chunk_index": index,
            "content": content,
            "start_offset": start,
            "end_offset": end,
            "char_count": end - start,
        })
        if end == len(text):
            break
        start += step
        index += 1

    return chunks


def persist_chunks(
    pool: ConnectionPool,
    document_id: str,
    chunks: list[dict],
) -> list[str]:
    """
    Insert chunks into the database. Skips duplicates (idempotent).

    Returns:
        List of chunk UUIDs (in chunk_index order).
    """
    if not chunks:
        return []

    chunk_ids: list[str] = []

    with pool.connection() as conn:
        with conn.cursor() as cur:
            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO chunks
                        (id, document_id, chunk_index, content, char_count,
                         start_offset, end_offset)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, chunk_index) DO NOTHING
                    RETURNING id
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk["chunk_index"],
                        chunk["content"],
                        chunk["char_count"],
                        chunk["start_offset"],
                        chunk["end_offset"],
                    ),
                )
                row = cur.fetchone()
                if row:
                    chunk_ids.append(str(row[0]))
                else:
                    # Fetch existing id on conflict
                    cur.execute(
                        "SELECT id FROM chunks WHERE document_id = %s AND chunk_index = %s",
                        (document_id, chunk["chunk_index"]),
                    )
                    existing = cur.fetchone()
                    chunk_ids.append(str(existing[0]))

    return chunk_ids


def ingest_text_document(
    pool: ConnectionPool,
    file_path: str | Path,
    source_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """
    End-to-end ingestion of a .txt or .md document.

    Registers the document, reads its text, chunks it, and persists chunks.

    Returns:
        dict with document_id, chunk_ids, is_new.
    """
    path = Path(file_path).resolve()
    document_id, is_new = register_document(pool, path, source_name, metadata)
    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    chunk_ids = persist_chunks(pool, document_id, chunks)
    return {
        "document_id": document_id,
        "chunk_ids": chunk_ids,
        "is_new": is_new,
    }
