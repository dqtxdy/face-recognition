"""Passive image quality gate for presentation-attack risk.

This module is intentionally conservative. It catches low-quality captures that
are unsafe for enrollment or verification demos, but it is not a substitute for
active liveness or a trained PAD model.
"""

from __future__ import annotations

from dataclasses import dataclass
import io

from PIL import Image, ImageFilter, ImageOps, ImageStat


@dataclass(frozen=True)
class QualityCheck:
    name: str
    value: float
    minimum: float | None = None
    maximum: float | None = None
    passed: bool = True

    def to_dict(self) -> dict[str, float | bool | str | None]:
        return {
            "name": self.name,
            "value": round(self.value, 6),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class PassiveLivenessReport:
    passed: bool
    score: float
    checks: tuple[QualityCheck, ...]
    verdict: str

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "score": round(self.score, 6),
            "verdict": self.verdict,
            "checks": [check.to_dict() for check in self.checks],
        }


def analyze_passive_liveness(image_bytes: bytes) -> PassiveLivenessReport:
    """Score capture quality before biometric matching.

    The checks focus on resolution, exposure, contrast, and edge energy. A flat
    screen grab, 1x1 placeholder, or extremely blurred image should fail.
    """

    with Image.open(io.BytesIO(image_bytes)) as raw_image:
        image = ImageOps.exif_transpose(raw_image).convert("RGB")

    width, height = image.size
    grayscale = ImageOps.grayscale(image)
    stat = ImageStat.Stat(grayscale)
    brightness = stat.mean[0] / 255.0
    contrast = stat.stddev[0] / 255.0
    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_energy = ImageStat.Stat(edges).mean[0] / 255.0
    saturation = ImageStat.Stat(image.convert("HSV").getchannel("S")).mean[0] / 255.0

    checks = (
        _min_check("min_dimension", min(width, height), 80.0),
        _range_check("exposure", brightness, 0.16, 0.88),
        _min_check("contrast", contrast, 0.045),
        _min_check("edge_energy", edge_energy, 0.012),
        _min_check("texture_signal", max(contrast, edge_energy, saturation * 0.6), 0.05),
    )
    score = sum(1.0 for check in checks if check.passed) / len(checks)
    passed = all(check.passed for check in checks)
    verdict = "passive-quality-pass" if passed else "passive-quality-review"
    return PassiveLivenessReport(
        passed=passed,
        score=score,
        checks=checks,
        verdict=verdict,
    )


def _min_check(name: str, value: float, minimum: float) -> QualityCheck:
    return QualityCheck(
        name=name,
        value=float(value),
        minimum=float(minimum),
        passed=float(value) >= float(minimum),
    )


def _range_check(
    name: str,
    value: float,
    minimum: float,
    maximum: float,
) -> QualityCheck:
    numeric = float(value)
    return QualityCheck(
        name=name,
        value=numeric,
        minimum=float(minimum),
        maximum=float(maximum),
        passed=float(minimum) <= numeric <= float(maximum),
    )
