"""Image loading and normalization helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def load_grayscale_image(path: str | Path, *, size: tuple[int, int] = (112, 112)) -> np.ndarray:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = image.resize(size, Image.Resampling.BILINEAR)
    array = np.asarray(image, dtype=np.float32) / 255.0
    return array


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    flat = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(flat)
    if norm == 0:
        return flat
    return flat / norm

