"""Optional deep face-recognition adapters.

The project can run its benchmark harness without these dependencies. Install
the relevant extras later when the team is ready to run real deep models.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from trustfacechain.image_io import normalize_vector


class OptionalModelDependencyError(RuntimeError):
    pass


def _missing(package: str, install_hint: str) -> OptionalModelDependencyError:
    return OptionalModelDependencyError(
        f"{package} is required for this model adapter. Install with: {install_hint}"
    )


class InsightFaceArcFaceEmbedder:
    """ArcFace-family adapter using InsightFace's FaceAnalysis app.

    Input images should be RGB or grayscale arrays. The adapter handles detection
    and returns the first detected face embedding.
    """

    name = "insightface"
    version = "buffalo_l"
    embedding_dim = 512

    def __init__(
        self,
        *,
        model_pack: str = "buffalo_l",
        provider: str = "CPUExecutionProvider",
        model_root: str | Path = "data/cache/insightface",
        bypass_detection: bool = False,
    ):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as error:
            raise _missing(
                "insightface",
                "python3 -m pip install insightface onnxruntime opencv-python",
            ) from error

        self.version = model_pack
        self.name = f"insightface-{model_pack}"
        self.bypass_detection = bypass_detection
        if self.bypass_detection:
            self.name = f"{self.name}-no-align"
        self._app = FaceAnalysis(name=self.version, root=str(model_root), providers=[provider])
        self._app.prepare(ctx_id=-1, det_size=(640, 640))
        self._recognition = self._app.models.get("recognition")

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        if self.bypass_detection or self._recognition is None:
            aligned = _as_rgb_uint8(image)
            from PIL import Image

            aligned = np.asarray(
                Image.fromarray(aligned).resize((112, 112), Image.Resampling.BILINEAR),
                dtype=np.uint8,
            )
            embedding = self._recognition.get_feat(aligned[:, :, ::-1])[0]
            return normalize_vector(np.asarray(embedding, dtype=np.float32))

        rgb = _as_rgb_uint8(image)
        bgr = rgb[:, :, ::-1]
        faces = self._app.get(bgr)
        if not faces:
            if self._recognition is None:
                raise ValueError("no face detected")
            aligned = _as_rgb_uint8(image)
            from PIL import Image

            aligned = np.asarray(
                Image.fromarray(aligned).resize((112, 112), Image.Resampling.BILINEAR),
                dtype=np.uint8,
            )
            embedding = self._recognition.get_feat(aligned[:, :, ::-1])[0]
            return normalize_vector(np.asarray(embedding, dtype=np.float32))
        return normalize_vector(np.asarray(faces[0].embedding, dtype=np.float32))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


class FaceNetPytorchEmbedder:
    """FaceNet adapter using facenet-pytorch's pretrained InceptionResnetV1."""

    name = "facenet-pytorch"
    version = "vggface2"
    embedding_dim = 512

    def __init__(self):
        try:
            import torch
            from facenet_pytorch import InceptionResnetV1
        except ImportError as error:
            raise _missing(
                "facenet-pytorch",
                "python3 -m pip install torch torchvision facenet-pytorch",
            ) from error

        self._torch = torch
        self._model = InceptionResnetV1(pretrained=self.version).eval()

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        rgb = _as_rgb_float(image, size=(160, 160))
        tensor = self._torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)
        tensor = (tensor - 0.5) / 0.5
        with self._torch.no_grad():
            embedding = self._model(tensor).detach().cpu().numpy()[0]
        return normalize_vector(embedding.astype(np.float32))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


class OnnxMobileFaceNetEmbedder:
    """MobileFaceNet-style adapter for an ONNX embedding model."""

    name = "mobilefacenet-onnx"
    version = "custom-onnx"

    def __init__(self, model_path: str | Path, *, input_name: str | None = None):
        try:
            import onnxruntime as ort
        except ImportError as error:
            raise _missing(
                "onnxruntime",
                "python3 -m pip install onnxruntime",
            ) from error

        self.model_path = str(model_path)
        self._session = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
        self._input_name = input_name or self._session.get_inputs()[0].name
        output_shape = self._session.get_outputs()[0].shape
        self.embedding_dim = int(output_shape[-1]) if isinstance(output_shape[-1], int) else 512

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        rgb = _as_rgb_float(image, size=(112, 112))
        tensor = np.transpose(rgb, (2, 0, 1))[None, :, :, :].astype(np.float32)
        tensor = (tensor - 0.5) / 0.5
        embedding = self._session.run(None, {self._input_name: tensor})[0][0]
        return normalize_vector(np.asarray(embedding, dtype=np.float32))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


def _as_rgb_uint8(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        image = np.repeat(image[:, :, None], 3, axis=2)
    if image.dtype != np.uint8:
        image = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    return image


def _as_rgb_float(image: np.ndarray, *, size: tuple[int, int]) -> np.ndarray:
    from PIL import Image

    rgb = _as_rgb_uint8(image)
    resized = Image.fromarray(rgb).resize(size, Image.Resampling.BILINEAR)
    return np.asarray(resized, dtype=np.float32) / 255.0
