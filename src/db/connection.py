"""
Database connection layer.

Provides a psycopg3 connection pool configured from environment variables.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

import psycopg
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

_REQUIRED_VARS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")

_pool: ConnectionPool | None = None


def _build_conninfo() -> str:
    missing = [v for v in _REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    return (
        f"host={os.environ['DB_HOST']} "
        f"port={os.environ['DB_PORT']} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )


def _configure_connection(conn: psycopg.Connection) -> None:
    """Register pgvector type on every new connection."""
    register_vector(conn)


def get_pool(min_size: int = 1, max_size: int = 5) -> ConnectionPool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        conninfo = _build_conninfo()
        _pool = ConnectionPool(
            conninfo,
            min_size=min_size,
            max_size=max_size,
            configure=_configure_connection,
            open=True,
        )
    return _pool


def close_pool() -> None:
    """Close the shared connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def execute(pool: ConnectionPool, query: str, params=None) -> list[tuple]:
    """Execute a query and return all rows."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []
