"""Tests for the database connection layer."""
from __future__ import annotations

import pytest
from psycopg_pool import ConnectionPool


def test_pool_initializes(pool):
    """Pool object is created successfully."""
    assert pool is not None
    assert isinstance(pool, ConnectionPool)


def test_connection_acquire(pool):
    """Can acquire a connection and run a basic query."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
    assert result == (1,)


def test_sql_execution(pool):
    """Can create a temp table, insert data, and select it back."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TEMP TABLE _test_conn (val TEXT) ON COMMIT DROP"
            )
            cur.execute("INSERT INTO _test_conn VALUES (%s)", ("hello",))
            cur.execute("SELECT val FROM _test_conn")
            rows = cur.fetchall()
    assert rows == [("hello",)]
