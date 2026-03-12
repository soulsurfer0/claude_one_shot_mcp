#!/usr/bin/env python3
"""Initialize the RAG database schema."""
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
import psycopg

def init_db():
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    schema_path = Path(__file__).parent.parent / "schema" / "init.sql"
    sql = schema_path.read_text(encoding="utf-8")

    conninfo = f"host={host} port={port} dbname={name} user={user} password={password}"
    print(f"Connecting to {host}:{port}/{name} ...")
    with psycopg.connect(conninfo) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Schema initialised successfully.")

if __name__ == "__main__":
    init_db()
