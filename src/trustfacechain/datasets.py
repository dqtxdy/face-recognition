"""Dataset loading and pair generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import random

import numpy as np

from trustfacechain.image_io import load_grayscale_image


@dataclass(frozen=True)
class FaceSample:
    sample_id: str
    identity: str
    image: np.ndarray
    path: str | None = None


@dataclass(frozen=True)
class FacePair:
    left: FaceSample
    right: FaceSample
    label: int


def load_folder_dataset(
    root: str | Path,
    *,
    image_size: tuple[int, int] = (112, 112),
) -> list[FaceSample]:
    """Load a folder dataset organized as root/person_name/image files."""

    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(root_path)

    samples: list[FaceSample] = []
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    for identity_dir in sorted(item for item in root_path.iterdir() if item.is_dir()):
        for image_path in sorted(identity_dir.iterdir()):
            if image_path.suffix.lower() not in extensions:
                continue
            image = load_grayscale_image(image_path, size=image_size)
            samples.append(
                FaceSample(
                    sample_id=str(image_path.relative_to(root_path)),
                    identity=identity_dir.name,
                    image=image,
                    path=str(image_path),
                )
            )

    if not samples:
        raise ValueError(f"no face images found under {root_path}")
    return samples


def load_pairs_csv(
    csv_path: str | Path,
    *,
    image_size: tuple[int, int] = (112, 112),
) -> list[FacePair]:
    """Load explicit pairs from CSV with left_path,right_path,label columns."""

    pairs: list[FacePair] = []
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"left_path", "right_path", "label"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing CSV columns: {sorted(missing)}")
        for index, row in enumerate(reader):
            left_path = Path(row["left_path"])
            right_path = Path(row["right_path"])
            label = int(row["label"])
            left_identity = row.get("left_identity") or left_path.parent.name
            right_identity = row.get("right_identity") or right_path.parent.name
            pairs.append(
                FacePair(
                    left=FaceSample(
                        sample_id=f"pair-{index}-left",
                        identity=left_identity,
                        image=load_grayscale_image(left_path, size=image_size),
                        path=str(left_path),
                    ),
                    right=FaceSample(
                        sample_id=f"pair-{index}-right",
                        identity=right_identity,
                        image=load_grayscale_image(right_path, size=image_size),
                        path=str(right_path),
                    ),
                    label=label,
                )
            )
    if not pairs:
        raise ValueError(f"no pairs found in {csv_path}")
    return pairs


def make_pairs(
    samples: list[FaceSample],
    *,
    pairs_per_identity: int = 2,
    impostor_pairs: int | None = None,
    seed: int = 7,
) -> list[FacePair]:
    rng = random.Random(seed)
    by_identity: dict[str, list[FaceSample]] = {}
    for sample in samples:
        by_identity.setdefault(sample.identity, []).append(sample)

    genuine: list[FacePair] = []
    for identity_samples in by_identity.values():
        if len(identity_samples) < 2:
            continue
        for _ in range(pairs_per_identity):
            left, right = rng.sample(identity_samples, 2)
            genuine.append(FacePair(left=left, right=right, label=1))

    identities = [identity for identity, items in by_identity.items() if items]
    if len(identities) < 2:
        raise ValueError("at least two identities are required for impostor pairs")
    impostor_count = impostor_pairs if impostor_pairs is not None else len(genuine)
    impostors: list[FacePair] = []
    for _ in range(impostor_count):
        left_identity, right_identity = rng.sample(identities, 2)
        impostors.append(
            FacePair(
                left=rng.choice(by_identity[left_identity]),
                right=rng.choice(by_identity[right_identity]),
                label=0,
            )
        )

    pairs = genuine + impostors
    rng.shuffle(pairs)
    if not pairs:
        raise ValueError("not enough samples to create pairs")
    return pairs


def make_synthetic_face_dataset(
    *,
    identities: int = 8,
    samples_per_identity: int = 4,
    image_size: tuple[int, int] = (112, 112),
    seed: int = 11,
) -> list[FaceSample]:
    """Create deterministic face-like arrays for smoke benchmarks.

    This is only for pipeline testing. It is not a scientific face dataset.
    """

    rng = np.random.default_rng(seed)
    height, width = image_size
    yy, xx = np.mgrid[0:height, 0:width]
    samples: list[FaceSample] = []
    for identity_index in range(identities):
        cx = width * (0.48 + rng.normal(0, 0.035))
        cy = height * (0.47 + rng.normal(0, 0.035))
        face_radius_x = width * (0.24 + rng.normal(0, 0.015))
        face_radius_y = height * (0.32 + rng.normal(0, 0.015))
        base = np.exp(-(((xx - cx) / face_radius_x) ** 2 + ((yy - cy) / face_radius_y) ** 2))
        eye_offset = width * (0.075 + rng.normal(0, 0.008))
        eye_y = cy - height * 0.08
        left_eye = np.exp(-(((xx - (cx - eye_offset)) / 5.0) ** 2 + ((yy - eye_y) / 3.0) ** 2))
        right_eye = np.exp(-(((xx - (cx + eye_offset)) / 5.0) ** 2 + ((yy - eye_y) / 3.0) ** 2))
        mouth_y = cy + height * (0.11 + rng.normal(0, 0.008))
        mouth = np.exp(-(((xx - cx) / 18.0) ** 2 + ((yy - mouth_y) / 3.5) ** 2))
        identity_image = base - 0.45 * (left_eye + right_eye) - 0.28 * mouth
        identity_image = (identity_image - identity_image.min()) / (
            identity_image.max() - identity_image.min()
        )

        for sample_index in range(samples_per_identity):
            noise = rng.normal(0, 0.035, size=(height, width))
            brightness = rng.normal(0, 0.025)
            image = np.clip(identity_image + noise + brightness, 0.0, 1.0).astype(np.float32)
            samples.append(
                FaceSample(
                    sample_id=f"synthetic-{identity_index}-{sample_index}",
                    identity=f"identity-{identity_index:03d}",
                    image=image,
                )
            )
    return samples


def load_lfw_people_dataset(
    *,
    min_faces_per_person: int = 2,
    image_size: tuple[int, int] = (112, 112),
    max_samples: int | None = None,
    data_home: str | Path = "data/cache/scikit_learn",
) -> list[FaceSample]:
    """Load LFW through scikit-learn.

    The first run may download data from the scikit-learn mirror.
    """

    from PIL import Image
    from sklearn.datasets import fetch_lfw_people

    lfw = fetch_lfw_people(
        min_faces_per_person=min_faces_per_person,
        color=False,
        resize=1.0,
        data_home=str(data_home),
    )
    samples: list[FaceSample] = []
    total = len(lfw.images) if max_samples is None else min(max_samples, len(lfw.images))
    for index in range(total):
        raw = lfw.images[index].astype(np.float32)
        raw = (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)
        image = Image.fromarray((raw * 255).astype(np.uint8), mode="L")
        image = image.resize(image_size, Image.Resampling.BILINEAR)
        identity = str(lfw.target_names[lfw.target[index]])
        samples.append(
            FaceSample(
                sample_id=f"lfw-{index}",
                identity=identity,
                image=np.asarray(image, dtype=np.float32) / 255.0,
            )
        )
    if not samples:
        raise ValueError("LFW loader returned no samples")
    return samples


def load_lfw_official_pairs(
    *,
    data_home: str | Path = "data/cache/scikit_learn",
    image_size: tuple[int, int] = (112, 112),
    max_pairs: int | None = None,
    balanced_subset: bool = True,
) -> list[FacePair]:
    """Load LFW official verification pairs after ensuring LFW is cached."""

    # Ensure the images are present. This may download the dataset on first run.
    load_lfw_people_dataset(data_home=data_home, image_size=image_size, max_samples=1)

    data_path = Path(data_home)
    lfw_home = data_path / "lfw_home"
    image_root = lfw_home / "lfw_funneled"
    pairs_path = image_root / "pairs.txt"
    if not pairs_path.exists():
        pairs_path = lfw_home / "pairs.txt"
    if not pairs_path.exists():
        raise FileNotFoundError("LFW pairs.txt not found after dataset fetch")

    pair_rows: list[tuple[str, int, str, int, int]] = []
    with pairs_path.open(encoding="utf-8") as handle:
        lines = [line.strip().split() for line in handle if line.strip()]

    for row in lines[1:]:
        if len(row) == 3:
            identity, left_index, right_index = row
            pair_rows.append((identity, int(left_index), identity, int(right_index), 1))
        elif len(row) == 4:
            identity, left_index, right_identity, right_index = row
            pair_rows.append((identity, int(left_index), right_identity, int(right_index), 0))
        else:
            continue

    if max_pairs is not None:
        if balanced_subset:
            wanted_positive = max_pairs // 2
            wanted_negative = max_pairs - wanted_positive
            positives = [row for row in pair_rows if row[-1] == 1][:wanted_positive]
            negatives = [row for row in pair_rows if row[-1] == 0][:wanted_negative]
            pair_rows = positives + negatives
        else:
            pair_rows = pair_rows[:max_pairs]

    pairs: list[FacePair] = []
    for identity, left_index, right_identity, right_index, label in pair_rows:
        left_path = _lfw_image_path(image_root, identity, left_index)
        right_path = _lfw_image_path(image_root, right_identity, right_index)
        if not left_path.exists() or not right_path.exists():
            continue
        pair_index = len(pairs)
        pairs.append(
            FacePair(
                left=FaceSample(
                    sample_id=f"lfw-official-{pair_index}-left",
                    identity=identity,
                    image=load_grayscale_image(left_path, size=image_size),
                    path=str(left_path),
                ),
                right=FaceSample(
                    sample_id=f"lfw-official-{pair_index}-right",
                    identity=right_identity,
                    image=load_grayscale_image(right_path, size=image_size),
                    path=str(right_path),
                ),
                label=label,
            )
        )

    if not pairs:
        raise ValueError("no LFW official pairs could be loaded")
    return pairs


def _lfw_image_path(root: Path, identity: str, index: int) -> Path:
    return root / identity / f"{identity}_{index:04d}.jpg"
