"""
Semantic retrieval layer.

Performs cosine similarity search using pgvector, returning the top-k
most relevant chunks for a given natural language query.
"""
from __future__ import annotations

from psycopg_pool import ConnectionPool

from src.embeddings.embedder import Embedder


def search(
    pool: ConnectionPool,
    query: str,
    embedder: Embedder,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve top-k chunks most similar to the query.

    Args:
        pool: Connection pool.
        query: Natural language query string.
        embedder: Embedder used for both document and query vectors.
        top_k: Number of results to return.

    Returns:
        List of dicts, each containing:
            chunk_id, document_id, source_name, chunk_index, content, similarity.
        Ordered by descending similarity (most relevant first).
    """
    query_vec = embedder.embed_one(query).tolist()

    sql = """
        SELECT
            c.id          AS chunk_id,
            c.document_id,
            d.source_name,
            c.chunk_index,
            c.content,
            1.0 - (ce.embedding <=> %s::vector) AS similarity
        FROM chunk_embeddings ce
        JOIN chunks    c ON ce.chunk_id   = c.id
        JOIN documents d ON c.document_id = d.id
        WHERE ce.embedding_model = %s
        ORDER BY ce.embedding <=> %s::vector
        LIMIT %s
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (query_vec, embedder.model_name, query_vec, top_k))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]

    return [dict(zip(cols, row)) for row in rows]
