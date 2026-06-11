"""Lightweight image embedders used before deep model adapters are installed."""

from __future__ import annotations

import numpy as np
from scipy.fftpack import dct
from sklearn.decomposition import PCA

from trustfacechain.image_io import normalize_vector


class PixelEmbedder:
    name = "pixel-cosine"
    version = "0.1.0"
    embedding_dim = 112 * 112

    def fit(self, images: list[np.ndarray]) -> None:
        if images:
            self.embedding_dim = int(images[0].size)

    def embed(self, image: np.ndarray) -> np.ndarray:
        centered = image.astype(np.float32) - float(np.mean(image))
        return normalize_vector(centered)

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


class DctEmbedder:
    name = "dct-low-frequency"
    version = "0.1.0"

    def __init__(self, keep: int = 24):
        self.keep = keep
        self.embedding_dim = keep * keep

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        coeffs = dct(dct(image.astype(np.float32), axis=0, norm="ortho"), axis=1, norm="ortho")
        low = coeffs[: self.keep, : self.keep]
        low = low - np.mean(low)
        return normalize_vector(low)

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


class LbpHistogramEmbedder:
    name = "lbp-histogram"
    version = "0.1.0"

    def __init__(self, grid: int = 7):
        self.grid = grid
        self.embedding_dim = grid * grid * 256

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        lbp = _lbp_codes(image.astype(np.float32))
        height, width = lbp.shape
        cell_h = height // self.grid
        cell_w = width // self.grid
        histograms: list[np.ndarray] = []
        for row in range(self.grid):
            for col in range(self.grid):
                cell = lbp[
                    row * cell_h : (row + 1) * cell_h,
                    col * cell_w : (col + 1) * cell_w,
                ]
                hist, _ = np.histogram(cell, bins=256, range=(0, 256), density=False)
                histograms.append(hist.astype(np.float32))
        return normalize_vector(np.concatenate(histograms))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        minimum = np.minimum(embedding_a, embedding_b)
        return float(np.sum(minimum))


class EigenfacesEmbedder:
    name = "eigenfaces-pca"
    version = "0.1.0"

    def __init__(self, components: int = 64):
        self.components = components
        self.embedding_dim = components
        self._pca: PCA | None = None

    def fit(self, images: list[np.ndarray]) -> None:
        if len(images) < 2:
            raise ValueError("EigenfacesEmbedder needs at least two images to fit PCA")
        flattened = np.stack([image.reshape(-1) for image in images])
        n_components = min(self.components, flattened.shape[0] - 1, flattened.shape[1])
        self.embedding_dim = int(n_components)
        self._pca = PCA(n_components=n_components, whiten=True, random_state=7)
        self._pca.fit(flattened)

    def embed(self, image: np.ndarray) -> np.ndarray:
        if self._pca is None:
            raise RuntimeError("EigenfacesEmbedder.fit must be called before embed")
        transformed = self._pca.transform(image.reshape(1, -1))[0]
        return normalize_vector(transformed.astype(np.float32))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


def create_embedder(name: str):
    normalized = name.strip().lower()
    if normalized in {"pixel", "pixel-cosine"}:
        return PixelEmbedder()
    if normalized in {"dct", "dct-low-frequency"}:
        return DctEmbedder()
    if normalized in {"lbp", "lbp-histogram"}:
        return LbpHistogramEmbedder()
    if normalized in {"eigenfaces", "pca", "eigenfaces-pca"}:
        return EigenfacesEmbedder()
    raise ValueError(f"unknown embedder: {name}")


def default_embedders():
    return [PixelEmbedder(), DctEmbedder(), LbpHistogramEmbedder(), EigenfacesEmbedder()]


def _lbp_codes(image: np.ndarray) -> np.ndarray:
    center = image[1:-1, 1:-1]
    codes = np.zeros_like(center, dtype=np.uint8)
    offsets = [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),
        (0, -1),
    ]
    for bit, (dy, dx) in enumerate(offsets):
        neighbor = image[1 + dy : image.shape[0] - 1 + dy, 1 + dx : image.shape[1] - 1 + dx]
        codes |= ((neighbor >= center).astype(np.uint8) << bit)
    return codes

