"""Model interfaces and starter embedders."""

from trustfacechain.models.base import FaceEmbedder
from trustfacechain.models.classical import (
    DctEmbedder,
    EigenfacesEmbedder,
    LbpHistogramEmbedder,
    PixelEmbedder,
)
from trustfacechain.models.hash_embedder import DeterministicHashEmbedder
from trustfacechain.models.siamese import SiameseEmbedder

__all__ = [
    "DctEmbedder",
    "DeterministicHashEmbedder",
    "EigenfacesEmbedder",
    "FaceEmbedder",
    "LbpHistogramEmbedder",
    "PixelEmbedder",
    "SiameseEmbedder",
]
