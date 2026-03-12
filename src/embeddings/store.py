"""
Embedding storage layer.

Persists embeddings to the chunk_embeddings table via pgvector.
Insertion is idempotent: duplicate (chunk_id, embedding_model) rows are skipped.
"""
from __future__ import annotations

import uuid

import numpy as np
from psycopg_pool import ConnectionPool

from src.embeddings.embedder import Embedder


def store_embeddings(
    pool: ConnectionPool,
    chunk_ids: list[str],
    embeddings: np.ndarray,
    embedder: Embedder,
) -> int:
    """
    Store pre-computed embeddings for a list of chunk IDs.

    Args:
        pool: Connection pool.
        chunk_ids: List of chunk UUID strings (same order as embeddings).
        embeddings: (N, dim) float32 ndarray.
        embedder: Embedder used to produce these embeddings.

    Returns:
        Number of newly inserted rows (0 if all already existed).

    Raises:
        ValueError: if embedding dimensions don't match embedder.dim.
    """
    if embeddings.shape[1] != embedder.dim:
        raise ValueError(
            f"Embedding dim mismatch: expected {embedder.dim}, "
            f"got {embeddings.shape[1]}"
        )

    inserted = 0
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for chunk_id, emb in zip(chunk_ids, embeddings):
                row_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO chunk_embeddings
                        (id, chunk_id, embedding_model, embedding_dim, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id, embedding_model) DO NOTHING
                    """,
                    (
                        row_id,
                        chunk_id,
                        embedder.model_name,
                        embedder.dim,
                        emb.tolist(),
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
    return inserted


def store_document_embeddings(
    pool: ConnectionPool,
    chunk_ids: list[str],
    contents: list[str],
    embedder: Embedder,
) -> int:
    """
    Generate embeddings for chunk contents and store them.

    Args:
        pool: Connection pool.
        chunk_ids: List of chunk UUID strings.
        contents: List of chunk text content (same order as chunk_ids).
        embedder: Embedder to use.

    Returns:
        Number of newly inserted embedding rows.
    """
    if not chunk_ids:
        return 0
    embeddings = embedder.embed(contents)
    return store_embeddings(pool, chunk_ids, embeddings, embedder)
