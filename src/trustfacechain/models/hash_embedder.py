"""Dependency-free mock embedder for early pipeline testing.

This is not a face-recognition model. It exists so the repository can test
metrics, template protection, and app wiring before heavyweight ML dependencies
are installed.
"""

from __future__ import annotations

import hashlib
import math


class DeterministicHashEmbedder:
    version = "0.1.0"

    def __init__(self, name: str = "deterministic-hash", embedding_dim: int = 128):
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        self.name = name
        self.embedding_dim = embedding_dim

    def embed(self, image_bytes: bytes) -> list[float]:
        chunks: list[float] = []
        counter = 0
        while len(chunks) < self.embedding_dim:
            digest = hashlib.sha256(image_bytes + counter.to_bytes(4, "big")).digest()
            for byte in digest:
                chunks.append((byte / 127.5) - 1.0)
                if len(chunks) == self.embedding_dim:
                    break
            counter += 1
        return _l2_normalize(chunks)

    def score(self, embedding_a: list[float], embedding_b: list[float]) -> float:
        if len(embedding_a) != len(embedding_b):
            raise ValueError("embeddings must have the same length")
        return sum(a * b for a, b in zip(embedding_a, embedding_b, strict=True))


def _l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]

