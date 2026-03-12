-- MCP RAG Server Database Schema
-- PostgreSQL 16 + pgvector

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_path   TEXT        NOT NULL,
    source_name   TEXT        NOT NULL,
    source_type   TEXT        NOT NULL,
    file_hash     TEXT        NOT NULL,
    metadata      JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_documents_file_hash UNIQUE (file_hash)
);

CREATE TABLE IF NOT EXISTS chunks (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id   UUID        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index   INTEGER     NOT NULL,
    content       TEXT        NOT NULL,
    char_count    INTEGER     NOT NULL,
    token_count   INTEGER,
    start_offset  INTEGER     NOT NULL,
    end_offset    INTEGER     NOT NULL,
    metadata      JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chunks_document_chunk UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id        UUID        NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding_model TEXT        NOT NULL,
    embedding_dim   INTEGER     NOT NULL,
    embedding       VECTOR(384) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chunk_embeddings_chunk_model UNIQUE (chunk_id, embedding_model)
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_hnsw
    ON chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
