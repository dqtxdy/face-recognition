"""Common model protocol."""

from __future__ import annotations

from typing import Protocol


class FaceEmbedder(Protocol):
    name: str
    version: str
    embedding_dim: int

    def embed(self, image_bytes: bytes) -> list[float]:
        """Return a normalized embedding vector for an aligned face."""

    def score(self, embedding_a: list[float], embedding_b: list[float]) -> float:
        """Return a similarity score where larger means more similar."""

