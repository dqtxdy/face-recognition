"""Benchmark orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
import csv
import json
from pathlib import Path

import numpy as np

from trustfacechain.datasets import FacePair, FaceSample, make_pairs
from trustfacechain.metrics import VerificationReport, evaluate_scores


@dataclass(frozen=True)
class ModelBenchmarkResult:
    model_name: str
    model_version: str
    embedding_dim: int
    pairs: int
    fit_seconds: float
    embed_seconds: float
    score_seconds: float
    report: VerificationReport

    def summary(self) -> dict[str, object]:
        return {
            "model": self.model_name,
            "version": self.model_version,
            "embedding_dim": self.embedding_dim,
            "pairs": self.pairs,
            "best_threshold": self.report.best_threshold,
            "accuracy": self.report.best_accuracy,
            "eer": self.report.eer,
            "eer_threshold": self.report.eer_threshold,
            "fit_seconds": self.fit_seconds,
            "embed_seconds": self.embed_seconds,
            "score_seconds": self.score_seconds,
        }


def benchmark_embedder(embedder, pairs: list[FacePair]) -> ModelBenchmarkResult:
    images = _unique_samples(pairs)
    start = perf_counter()
    if hasattr(embedder, "fit"):
        embedder.fit([sample.image for sample in images])
    fit_seconds = perf_counter() - start

    start = perf_counter()
    embeddings = {sample.sample_id: embedder.embed(sample.image) for sample in images}
    embed_seconds = perf_counter() - start

    scores: list[float] = []
    labels: list[int] = []
    start = perf_counter()
    for pair in pairs:
        scores.append(
            embedder.score(
                embeddings[pair.left.sample_id],
                embeddings[pair.right.sample_id],
            )
        )
        labels.append(pair.label)
    score_seconds = perf_counter() - start

    report = evaluate_scores(scores=scores, labels=labels)
    return ModelBenchmarkResult(
        model_name=embedder.name,
        model_version=embedder.version,
        embedding_dim=int(embedder.embedding_dim),
        pairs=len(pairs),
        fit_seconds=fit_seconds,
        embed_seconds=embed_seconds,
        score_seconds=score_seconds,
        report=report,
    )


def benchmark_dataset(
    samples: list[FaceSample],
    embedders: list[object],
    *,
    pairs_per_identity: int = 2,
    impostor_pairs: int | None = None,
    seed: int = 7,
) -> list[ModelBenchmarkResult]:
    pairs = make_pairs(
        samples,
        pairs_per_identity=pairs_per_identity,
        impostor_pairs=impostor_pairs,
        seed=seed,
    )
    return [benchmark_embedder(embedder, pairs) for embedder in embedders]


def write_summary_csv(results: list[ModelBenchmarkResult], path: str | Path) -> None:
    rows = [result.summary() for result in results]
    if not rows:
        raise ValueError("no results to write")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report_json(results: list[ModelBenchmarkResult], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            **result.summary(),
            "operating_points": result.report.to_dict()["operating_points"],
        }
        for result in results
    ]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _unique_samples(pairs: list[FacePair]) -> list[FaceSample]:
    samples: dict[str, FaceSample] = {}
    for pair in pairs:
        samples[pair.left.sample_id] = pair.left
        samples[pair.right.sample_id] = pair.right
    return list(samples.values())

