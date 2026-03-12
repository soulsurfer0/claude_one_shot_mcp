"""Tests for the embedding model."""
from __future__ import annotations

import numpy as np
import pytest


def test_embedding_shape(embedder):
    """embed() returns (N, 384) array."""
    texts = ["Hello world", "Another text"]
    result = embedder.embed(texts)
    assert result.shape == (2, 384)


def test_embed_one_shape(embedder):
    """embed_one() returns (384,) array."""
    result = embedder.embed_one("Single text")
    assert result.shape == (384,)


def test_batch_embedding(embedder):
    """Batch of 3 texts returns (3, 384) array."""
    texts = ["First", "Second", "Third"]
    result = embedder.embed(texts)
    assert result.shape == (3, 384)


def test_embed_empty_list(embedder):
    """Empty list returns (0, 384) array."""
    result = embedder.embed([])
    assert result.shape == (0, 384)


def test_embedding_dtype(embedder):
    """Embeddings are float32."""
    result = embedder.embed_one("test")
    assert result.dtype == np.float32


def test_embedding_normalized(embedder):
    """Embeddings are L2-normalized (norm ≈ 1.0)."""
    result = embedder.embed_one("normalized test")
    norm = float(np.linalg.norm(result))
    assert abs(norm - 1.0) < 1e-4


def test_model_name(embedder):
    assert "bge" in embedder.model_name.lower() or "BAAI" in embedder.model_name


def test_dim_property(embedder):
    assert embedder.dim == 384
