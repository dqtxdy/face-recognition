"""Ablation study runner for face recognition models."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from time import perf_counter

import numpy as np

from trustfacechain.benchmark import benchmark_embedder
from trustfacechain.datasets import FacePair, FaceSample
from trustfacechain.models.deep_adapters import InsightFaceArcFaceEmbedder, FaceNetPytorchEmbedder
from trustfacechain.models.classical import DctEmbedder, LbpHistogramEmbedder, EigenfacesEmbedder
from trustfacechain.models.siamese import SiameseEmbedder

logger = logging.getLogger(__name__)


def downscale_pairs(pairs: list[FacePair], size: int) -> list[FacePair]:
    """Simulate low-resolution inputs by downscaling and upscaling probe images."""
    from PIL import Image

    corrupted_pairs = []
    for pair in pairs:
        left_img = _resize_and_back(pair.left.image, size)
        right_img = _resize_and_back(pair.right.image, size)
        corrupted_pairs.append(
            FacePair(
                left=FaceSample(
                    sample_id=f"{pair.left.sample_id}:res-{size}",
                    identity=pair.left.identity,
                    image=left_img,
                    path=pair.left.path,
                ),
                right=FaceSample(
                    sample_id=f"{pair.right.sample_id}:res-{size}",
                    identity=pair.right.identity,
                    image=right_img,
                    path=pair.right.path,
                ),
                label=pair.label,
            )
        )
    return corrupted_pairs


def _resize_and_back(arr: np.ndarray, size: int) -> np.ndarray:
    from PIL import Image

    # arr is float32 grayscale, shape (112, 112)
    img = Image.fromarray((arr * 255).astype(np.uint8), mode="L")
    small = img.resize((size, size), Image.Resampling.BILINEAR)
    restored = small.resize((112, 112), Image.Resampling.BILINEAR)
    return np.asarray(restored, dtype=np.float32) / 255.0


def run_ablation_suite(pairs: list[FacePair], output_csv: str | Path = "reports/ablation_results.csv") -> list[dict[str, object]]:
    """Execute the systematic ablation study suite and output a CSV report."""
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []

    logger.info("Initializing ablation study models...")
    # Define the ablation conditions
    conditions = [
        {
            "name": "Buffalo-S (Baseline)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_s", bypass_detection=False),
            "pairs": pairs,
            "category": "Alignment",
            "condition": "With Alignment",
        },
        {
            "name": "Buffalo-S (No Alignment)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_s", bypass_detection=True),
            "pairs": pairs,
            "category": "Alignment",
            "condition": "Without Alignment",
        },
        {
            "name": "Buffalo-S (Resolution 56x56)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_s", bypass_detection=False),
            "pairs": downscale_pairs(pairs, 56),
            "category": "Resolution",
            "condition": "56x56",
        },
        {
            "name": "Buffalo-S (Resolution 28x28)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_s", bypass_detection=False),
            "pairs": downscale_pairs(pairs, 28),
            "category": "Resolution",
            "condition": "28x28",
        },
        {
            "name": "Buffalo-L (Baseline)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_l", bypass_detection=False),
            "pairs": pairs,
            "category": "Model Size",
            "condition": "buffalo_l",
        },
        {
            "name": "Buffalo-L (No Alignment)",
            "embedder": InsightFaceArcFaceEmbedder(model_pack="buffalo_l", bypass_detection=True),
            "pairs": pairs,
            "category": "Model Size & Alignment",
            "condition": "buffalo_l-no-align",
        },
        {
            "name": "FaceNet (Baseline)",
            "embedder": FaceNetPytorchEmbedder(),
            "pairs": pairs,
            "category": "Architecture",
            "condition": "InceptionResnetV1",
        },
        {
            "name": "Eigenfaces PCA (Classical)",
            "embedder": EigenfacesEmbedder(),
            "pairs": pairs,
            "category": "Classical Baseline",
            "condition": "PCA",
        },
        {
            "name": "LBP Histogram (Classical)",
            "embedder": LbpHistogramEmbedder(),
            "pairs": pairs,
            "category": "Classical Baseline",
            "condition": "Local Binary Patterns",
        },
        {
            "name": "DCT Low-Frequency (Classical)",
            "embedder": DctEmbedder(),
            "pairs": pairs,
            "category": "Classical Baseline",
            "condition": "Discrete Cosine Transform",
        },
    ]

    # Try to add Siamese model if trained
    try:
        siamese_emb = SiameseEmbedder()
        conditions.append({
            "name": "Self-Trained Siamese CNN",
            "embedder": siamese_emb,
            "pairs": pairs,
            "category": "Architecture",
            "condition": "Siamese CNN",
        })
    except Exception as e:
        logger.warning(f"Could not load Siamese embedder for ablation: {e}")

    logger.info(f"Running {len(conditions)} ablation experiments on {len(pairs)} pairs...")

    for cond in conditions:
        name = cond["name"]
        embedder = cond["embedder"]
        cond_pairs = cond["pairs"]

        logger.info(f"Running experiment: {name}...")
        start_time = perf_counter()
        res = benchmark_embedder(embedder, cond_pairs)
        latency = perf_counter() - start_time

        results.append({
            "experiment": name,
            "category": cond["category"],
            "condition": cond["condition"],
            "accuracy": res.report.best_accuracy,
            "eer": res.report.eer,
            "precision": res.report.best_precision,
            "recall": res.report.best_recall,
            "f1_score": res.report.best_f1_score,
            "auc": res.report.auc,
            "latency_seconds": latency,
            "embed_seconds": res.embed_seconds,
        })

    # Save to CSV
    if results:
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Ablation results successfully written to {output_path}")

    return results
