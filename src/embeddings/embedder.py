"""
Embedding model abstraction.

Provides a model-agnostic Embedder interface and a BGE implementation
using sentence-transformers. Supports batch embedding generation.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod

import numpy as np


class Embedder(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for a list of texts. Returns (N, dim) array."""

    @abstractmethod
    def embed_one(self, text: str) -> np.ndarray:
        """Generate embedding for a single text. Returns (dim,) array."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier string for this embedding model."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Embedding dimensionality."""


class BGEEmbedder(Embedder):
    """
    Sentence-Transformers embedder using BAAI/bge-small-en-v1.5.
    Produces 384-dimensional embeddings.
    """

    _DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name or os.environ.get(
            "EMBEDDING_MODEL", self._DEFAULT_MODEL
        )
        self._model = SentenceTransformer(self._model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return (N, dim) float32 array of embeddings."""
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype(np.float32)

    def embed_one(self, text: str) -> np.ndarray:
        """Return (dim,) float32 embedding for a single text."""
        return self.embed([text])[0]

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim


_default_embedder: BGEEmbedder | None = None


def get_default_embedder() -> BGEEmbedder:
    """Return the shared default BGEEmbedder (lazy singleton)."""
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = BGEEmbedder()
    return _default_embedder
