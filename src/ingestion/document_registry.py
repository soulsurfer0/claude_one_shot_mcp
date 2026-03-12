"""
Document registry.

Handles deterministic, content-addressed document registration in PostgreSQL.
Documents are identified by the SHA256 hash of their content, making ingestion
idempotent: re-ingesting identical content returns the existing document_id.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool


_CHUNK_SIZE = 65536  # 64 KiB reads for hashing

_SOURCE_TYPES: dict[str, str] = {
    ".txt": "text/plain",
    ".md":  "text/markdown",
    ".pdf": "application/pdf",
}


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hex digest of a file using chunked reads."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def infer_source_type(path: Path) -> str:
    """Infer MIME-ish source type from file extension."""
    return _SOURCE_TYPES.get(path.suffix.lower(), "application/octet-stream")


def register_document(
    pool: ConnectionPool,
    file_path: str | Path,
    source_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    """
    Register a document in the database.

    Returns:
        (document_id, is_new): UUID string and whether this was a new insertion.

    Raises:
        FileNotFoundError: if the file does not exist.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    name = source_name or path.name
    source_type = infer_source_type(path)
    file_hash = compute_file_hash(path)
    meta = metadata or {}

    with pool.connection() as conn:
        with conn.cursor() as cur:
            # Attempt insert; do nothing on hash conflict
            cur.execute(
                """
                INSERT INTO documents (source_path, source_name, source_type, file_hash, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (file_hash) DO NOTHING
                RETURNING id
                """,
                (str(path), name, source_type, file_hash, Jsonb(meta)),
            )
            row = cur.fetchone()
            if row:
                return str(row[0]), True

            # Conflict: fetch existing id
            cur.execute(
                "SELECT id FROM documents WHERE file_hash = %s",
                (file_hash,),
            )
            row = cur.fetchone()
            return str(row[0]), False
