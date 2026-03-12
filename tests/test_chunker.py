"""Tests for the chunker — pure chunking logic (no DB)."""
from __future__ import annotations

import pytest

from src.ingestion.chunker import chunk_text, CHUNK_SIZE, OVERLAP


def test_empty_input():
    assert chunk_text("") == []


def test_whitespace_only():
    assert chunk_text("   \n\t  ") == []


def test_short_text():
    """Text shorter than chunk_size produces exactly one chunk."""
    text = "Short text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0]["content"] == text
    assert chunks[0]["start_offset"] == 0
    assert chunks[0]["end_offset"] == len(text)
    assert chunks[0]["char_count"] == len(text)
    assert chunks[0]["chunk_index"] == 0


def test_exact_chunk_size():
    """Text exactly chunk_size chars produces one chunk."""
    text = "x" * CHUNK_SIZE
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0]["char_count"] == CHUNK_SIZE


def test_multiple_chunks():
    """Text longer than chunk_size produces multiple chunks."""
    text = "a" * (CHUNK_SIZE * 3)
    chunks = chunk_text(text)
    assert len(chunks) > 1


def test_overlap_correctness():
    """Consecutive chunks overlap by exactly OVERLAP characters."""
    text = "b" * (CHUNK_SIZE * 3)
    chunks = chunk_text(text)
    for i in range(len(chunks) - 1):
        step = chunks[i + 1]["start_offset"] - chunks[i]["start_offset"]
        assert step == CHUNK_SIZE - OVERLAP


def test_exact_offsets():
    """start_offset inclusive, end_offset exclusive; char_count = end - start."""
    text = "c" * (CHUNK_SIZE + 500)
    chunks = chunk_text(text)
    for chunk in chunks:
        assert chunk["char_count"] == chunk["end_offset"] - chunk["start_offset"]


def test_exact_slice_preservation():
    """Chunk content exactly matches the source text slice."""
    text = "".join(str(i % 10) for i in range(CHUNK_SIZE * 2))
    chunks = chunk_text(text)
    for chunk in chunks:
        assert chunk["content"] == text[chunk["start_offset"]:chunk["end_offset"]]


def test_chunk_index_sequential():
    """Chunk indices are sequential starting from 0."""
    text = "d" * (CHUNK_SIZE * 3)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i


def test_invalid_chunk_size_zero():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=0)


def test_invalid_chunk_size_negative():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=-1)


def test_invalid_overlap_negative():
    with pytest.raises(ValueError):
        chunk_text("text", overlap=-1)


def test_invalid_overlap_gte_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)
