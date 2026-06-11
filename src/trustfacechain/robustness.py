"""Robustness evaluation for degraded probe images."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from trustfacechain.benchmark import ModelBenchmarkResult, benchmark_embedder
from trustfacechain.datasets import FacePair, FaceSample


@dataclass(frozen=True)
class RobustnessResult:
    corruption: str
    level: float
    benchmark: ModelBenchmarkResult

    def summary(self) -> dict[str, object]:
        return {
            "corruption": self.corruption,
            "level": self.level,
            **self.benchmark.summary(),
        }


def corruption_suite() -> dict[str, list[float]]:
    return {
        "brightness_down": [0.15, 0.3, 0.45],
        "brightness_up": [0.15, 0.3, 0.45],
        "gaussian_noise": [0.03, 0.06, 0.1],
        "blur": [1.0, 2.0, 3.0],
        "jpeg": [70, 45, 25],
        "downscale": [0.75, 0.5, 0.25],
        "lower_occlusion": [0.15, 0.25, 0.35],
    }


def evaluate_robustness(
    *,
    pairs: list[FacePair],
    embedders: list[object],
    corruptions: dict[str, list[float]] | None = None,
) -> list[RobustnessResult]:
    selected = corruptions or corruption_suite()
    results: list[RobustnessResult] = []
    for corruption, levels in selected.items():
        for level in levels:
            corrupted_pairs = [
                FacePair(
                    left=pair.left,
                    right=FaceSample(
                        sample_id=f"{pair.right.sample_id}:{corruption}:{level}",
                        identity=pair.right.identity,
                        image=apply_corruption(pair.right.image, corruption=corruption, level=level),
                        path=pair.right.path,
                    ),
                    label=pair.label,
                )
                for pair in pairs
            ]
            for embedder in embedders:
                results.append(
                    RobustnessResult(
                        corruption=corruption,
                        level=level,
                        benchmark=benchmark_embedder(embedder, corrupted_pairs),
                    )
                )
    return results


def write_robustness_csv(results: list[RobustnessResult], path: str | Path) -> None:
    import csv

    rows = [result.summary() for result in results]
    if not rows:
        raise ValueError("no robustness results to write")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def apply_corruption(image: np.ndarray, *, corruption: str, level: float) -> np.ndarray:
    if corruption == "brightness_down":
        return np.clip(image * (1.0 - level), 0.0, 1.0).astype(np.float32)
    if corruption == "brightness_up":
        return np.clip(image + level, 0.0, 1.0).astype(np.float32)
    if corruption == "gaussian_noise":
        rng = np.random.default_rng(12345)
        return np.clip(image + rng.normal(0, level, size=image.shape), 0.0, 1.0).astype(np.float32)
    if corruption == "blur":
        pil = _to_pil(image).filter(ImageFilter.GaussianBlur(radius=level))
        return _from_pil(pil)
    if corruption == "jpeg":
        buffer = BytesIO()
        _to_pil(image).save(buffer, format="JPEG", quality=int(level))
        buffer.seek(0)
        return _from_pil(Image.open(buffer).convert("L"))
    if corruption == "downscale":
        pil = _to_pil(image)
        width, height = pil.size
        small = pil.resize(
            (max(1, int(width * level)), max(1, int(height * level))),
            Image.Resampling.BILINEAR,
        )
        return _from_pil(small.resize((width, height), Image.Resampling.BILINEAR))
    if corruption == "lower_occlusion":
        corrupted = image.copy()
        rows = int(corrupted.shape[0] * level)
        corrupted[-rows:, :] = float(np.mean(corrupted))
        return corrupted.astype(np.float32)
    raise ValueError(f"unknown corruption: {corruption}")


def _to_pil(image: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(image * 255.0, 0, 255).astype(np.uint8), mode="L")


def _from_pil(image: Image.Image) -> np.ndarray:
    return np.asarray(image, dtype=np.float32) / 255.0

