"""Product-grade enroll/verify/revoke service logic."""

from __future__ import annotations

import base64
import binascii
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from cryptography.fernet import Fernet

from trustfacechain.crypto import canonical_json_hash, sha256_hex
from trustfacechain.liveness import analyze_passive_liveness
from trustfacechain.models.hash_embedder import DeterministicHashEmbedder
from trustfacechain.store import ProductStore, StoredEvent, StoredIdentity
from trustfacechain.templates import TemplateProtector


class ProductServiceError(RuntimeError):
    pass


class IdentityAlreadyActive(ProductServiceError):
    pass


class IdentityNotFound(ProductServiceError):
    pass


class IdentityRevoked(ProductServiceError):
    pass


class InvalidBiometricInput(ProductServiceError):
    pass


class UnsupportedModelVersion(ProductServiceError):
    pass


class LivenessCheckFailed(ProductServiceError):
    pass


@dataclass(frozen=True)
class BiometricSample:
    kind: str
    data: bytes


@dataclass(frozen=True)
class EnrollmentResult:
    subject_id: str
    model_version: str
    template_commitment: str
    consent_hash: str
    event_hash: str
    liveness: dict[str, Any] | None = None


@dataclass(frozen=True)
class VerificationResult:
    subject_id: str
    model_version: str
    score: float
    threshold: float
    accepted: bool
    verification_hash: str
    liveness: dict[str, Any] | None = None


@dataclass(frozen=True)
class RevocationResult:
    subject_id: str
    reason_hash: str
    event_hash: str


class TrustFaceProductService:
    def __init__(
        self,
        *,
        store: ProductStore,
        fernet: Fernet,
        app_salt: bytes = b"trustfacechain-product",
    ):
        self.store = store
        self.fernet = fernet
        self.protector = TemplateProtector(app_salt=app_salt)
        self._image_embedders: dict[str, Any] = {}

    def enroll(
        self,
        *,
        subject_id: str,
        biometric_input: str | None = None,
        image_base64: str | None = None,
        model_version: str,
        consent: dict[str, Any],
        allow_reenroll: bool = False,
        require_liveness: bool = False,
    ) -> EnrollmentResult:
        existing = self.store.get_identity(subject_id)
        if existing and not existing.revoked and not allow_reenroll:
            raise IdentityAlreadyActive(subject_id)

        sample = _coerce_biometric_sample(
            biometric_input=biometric_input,
            image_base64=image_base64,
        )
        liveness = self._passive_liveness(sample, require_liveness=require_liveness)
        embedding = self._embed(model_version, sample)
        protected = self.protector.protect(
            subject_id=subject_id,
            model_version=model_version,
            embedding=embedding,
        )
        consent_payload = {
            **consent,
            "subjectId": subject_id,
            "modelVersion": model_version,
            "biometricPayload": sample.kind,
            "rawImageStorage": "none",
            "templateStorage": "encrypted-local",
            "passiveLiveness": _liveness_policy(liveness, require_liveness),
        }
        consent_hash = canonical_json_hash(consent_payload)
        encrypted_embedding = self.fernet.encrypt(_embedding_to_bytes(embedding))

        if existing:
            identity = self.store.replace_identity(
                subject_id=subject_id,
                model_version=model_version,
                template_commitment=protected.commitment,
                template_salt=protected.template_salt,
                consent_hash=consent_hash,
                encrypted_embedding=encrypted_embedding,
            )
        else:
            identity = self.store.create_identity(
                subject_id=subject_id,
                model_version=model_version,
                template_commitment=protected.commitment,
                template_salt=protected.template_salt,
                consent_hash=consent_hash,
                encrypted_embedding=encrypted_embedding,
            )

        event_hash = self._event_hash(
            "IdentityEnrolled",
            subject_id,
            {
                "templateCommitment": identity.template_commitment,
                "consentHash": identity.consent_hash,
                "modelVersion": identity.model_version,
                "livenessVerdict": _liveness_verdict(liveness),
            },
        )
        self.store.add_event(
            event_type="IdentityEnrolled",
            subject_id=subject_id,
            payload={
                "templateCommitment": identity.template_commitment,
                "consentHash": identity.consent_hash,
                "modelVersion": identity.model_version,
                "eventHash": event_hash,
                "liveness": liveness,
            },
        )
        return EnrollmentResult(
            subject_id=subject_id,
            model_version=model_version,
            template_commitment=identity.template_commitment,
            consent_hash=identity.consent_hash,
            event_hash=event_hash,
            liveness=liveness,
        )

    def verify(
        self,
        *,
        subject_id: str,
        biometric_input: str | None = None,
        image_base64: str | None = None,
        threshold: float,
        require_liveness: bool = False,
    ) -> VerificationResult:
        identity = self._require_active_identity(subject_id)
        reference_embedding = _embedding_from_bytes(
            self.fernet.decrypt(identity.encrypted_embedding)
        )
        sample = _coerce_biometric_sample(
            biometric_input=biometric_input,
            image_base64=image_base64,
        )
        liveness = self._passive_liveness(sample, require_liveness=require_liveness)
        probe_embedding = self._embed(identity.model_version, sample)
        score = _dot(reference_embedding, probe_embedding)
        accepted = score >= threshold
        verification_hash = self._event_hash(
            "VerificationLogged",
            subject_id,
            {
                "modelVersion": identity.model_version,
                "accepted": accepted,
                "threshold": round(threshold, 6),
                "scoreBucket": _score_bucket(score),
                "livenessVerdict": _liveness_verdict(liveness),
            },
        )
        self.store.add_event(
            event_type="VerificationLogged",
            subject_id=subject_id,
            payload={
                "verificationHash": verification_hash,
                "modelVersion": identity.model_version,
                "accepted": accepted,
                "threshold": threshold,
                "scoreBucket": _score_bucket(score),
                "liveness": liveness,
            },
        )
        return VerificationResult(
            subject_id=subject_id,
            model_version=identity.model_version,
            score=score,
            threshold=threshold,
            accepted=accepted,
            verification_hash=verification_hash,
            liveness=liveness,
        )

    def revoke(self, *, subject_id: str, reason: str) -> RevocationResult:
        identity = self.store.get_identity(subject_id)
        if not identity:
            raise IdentityNotFound(subject_id)
        if identity.revoked:
            raise IdentityRevoked(subject_id)
        reason_hash = sha256_hex(reason.encode("utf-8"))
        self.store.revoke_identity(subject_id)
        event_hash = self._event_hash(
            "TemplateRevoked",
            subject_id,
            {"reasonHash": reason_hash},
        )
        self.store.add_event(
            event_type="TemplateRevoked",
            subject_id=subject_id,
            payload={
                "reasonHash": reason_hash,
                "eventHash": event_hash,
            },
        )
        return RevocationResult(
            subject_id=subject_id,
            reason_hash=reason_hash,
            event_hash=event_hash,
        )

    def get_identity(self, subject_id: str) -> StoredIdentity | None:
        return self.store.get_identity(subject_id)

    def list_events(
        self,
        *,
        subject_id: str | None = None,
        limit: int = 100,
    ) -> list[StoredEvent]:
        return self.store.list_events(subject_id=subject_id, limit=limit)

    def metrics(self) -> dict[str, int]:
        return self.store.metrics()

    def _require_active_identity(self, subject_id: str) -> StoredIdentity:
        identity = self.store.get_identity(subject_id)
        if not identity:
            raise IdentityNotFound(subject_id)
        if identity.revoked:
            raise IdentityRevoked(subject_id)
        return identity

    def _embed(self, model_version: str, sample: BiometricSample) -> list[float]:
        if sample.kind == "text":
            return _embed_text(model_version, sample.data.decode("utf-8"))
        return self._embed_image(model_version, sample.data)

    def _passive_liveness(
        self,
        sample: BiometricSample,
        *,
        require_liveness: bool,
    ) -> dict[str, Any] | None:
        if sample.kind != "image_base64":
            if require_liveness:
                raise InvalidBiometricInput("passive liveness requires image_base64 input")
            return None

        try:
            report = analyze_passive_liveness(sample.data).to_dict()
        except OSError as error:
            raise InvalidBiometricInput("image_base64 does not decode to an image") from error
        if require_liveness and not report["passed"]:
            failed = [
                check["name"]
                for check in report["checks"]
                if isinstance(check, dict) and not check.get("passed")
            ]
            detail = ", ".join(failed) or "capture quality"
            raise LivenessCheckFailed(f"passive liveness gate failed: {detail}")
        return report

    def _embed_image(self, model_version: str, image_bytes: bytes) -> list[float]:
        if model_version in {"demo-hash-v1", "demo-image-hash-v1"}:
            canonical = _canonical_image_bytes(image_bytes)
            embedder = DeterministicHashEmbedder(name=model_version, embedding_dim=128)
            return embedder.embed(canonical)

        if model_version == "facenet":
            embedder = self._image_embedders.get(model_version)
            if embedder is None:
                try:
                    from trustfacechain.models.deep_adapters import FaceNetPytorchEmbedder
                    embedder = FaceNetPytorchEmbedder()
                except RuntimeError as error:
                    raise UnsupportedModelVersion(str(error)) from error
                self._image_embedders[model_version] = embedder
            try:
                embedding = embedder.embed(_image_bytes_to_rgb_array(image_bytes))
            except ValueError as error:
                raise InvalidBiometricInput(str(error)) from error
            return [float(value) for value in embedding.tolist()]

        model_pack = _insightface_pack_for(model_version)
        if model_pack is None:
            raise UnsupportedModelVersion(
                f"{model_version} is not supported for image inference"
            )

        embedder = self._image_embedders.get(model_version)
        if embedder is None:
            try:
                from trustfacechain.models.deep_adapters import InsightFaceArcFaceEmbedder
            except ImportError as error:
                raise ProductServiceError(
                    "InsightFace image inference dependencies are not installed"
                ) from error
            embedder = InsightFaceArcFaceEmbedder(model_pack=model_pack)
            self._image_embedders[model_version] = embedder

        try:
            embedding = embedder.embed(_image_bytes_to_rgb_array(image_bytes))
        except ValueError as error:
            raise InvalidBiometricInput(str(error)) from error
        return [float(value) for value in embedding.tolist()]

    def _event_hash(
        self,
        event_type: str,
        subject_id: str,
        payload: dict[str, Any],
    ) -> str:
        return canonical_json_hash(
            {
                "eventType": event_type,
                "subjectId": subject_id,
                "payload": payload,
            }
        )


def build_product_service(
    *,
    db_path: str | Path = "data/runtime/trustfacechain.db",
    key_path: str | Path = "data/runtime/fernet.key",
) -> TrustFaceProductService:
    return TrustFaceProductService(
        store=ProductStore(db_path),
        fernet=Fernet(_load_or_create_key(key_path)),
    )


def _load_or_create_key(key_path: str | Path) -> bytes:
    env_key = os.environ.get("TRUSTFACECHAIN_FERNET_KEY")
    if env_key:
        return env_key.encode("utf-8")
    path = Path(key_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path.read_bytes().strip()
    key = Fernet.generate_key()
    path.write_bytes(key)
    return key


def _embed_text(model_version: str, text: str) -> list[float]:
    if _insightface_pack_for(model_version) is not None or model_version == "facenet":
        raise InvalidBiometricInput(
            f"{model_version} requires image_base64 input, not biometric_input text"
        )
    embedder = DeterministicHashEmbedder(name=model_version, embedding_dim=128)
    return embedder.embed(text.encode("utf-8"))


def _coerce_biometric_sample(
    *,
    biometric_input: str | None,
    image_base64: str | None,
) -> BiometricSample:
    has_text = bool(biometric_input and biometric_input.strip())
    has_image = bool(image_base64 and image_base64.strip())
    if has_text == has_image:
        raise InvalidBiometricInput(
            "provide exactly one of biometric_input or image_base64"
        )
    if has_text:
        return BiometricSample(kind="text", data=biometric_input.strip().encode("utf-8"))
    return BiometricSample(kind="image_base64", data=_decode_image_base64(image_base64 or ""))


def _decode_image_base64(payload: str) -> bytes:
    encoded = payload.strip()
    if "," in encoded and encoded.lower().startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    encoded = "".join(encoded.split())
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise InvalidBiometricInput("image_base64 is not valid base64") from error
    if not image_bytes:
        raise InvalidBiometricInput("image_base64 is empty")
    return image_bytes


def _canonical_image_bytes(image_bytes: bytes) -> bytes:
    from PIL import Image, ImageOps

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            image = image.resize((112, 112), Image.Resampling.BILINEAR)
            return image.tobytes()
    except OSError as error:
        raise InvalidBiometricInput("image_base64 does not decode to an image") from error


def _image_bytes_to_rgb_array(image_bytes: bytes) -> Any:
    import numpy as np
    from PIL import Image, ImageOps

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            return np.asarray(image, dtype=np.uint8)
    except OSError as error:
        raise InvalidBiometricInput("image_base64 does not decode to an image") from error


def _insightface_pack_for(model_version: str) -> str | None:
    return {
        "arcface": "buffalo_l",
        "buffalo_l": "buffalo_l",
        "insightface-buffalo_l": "buffalo_l",
        "buffalo_s": "buffalo_s",
        "mobileface": "buffalo_s",
        "insightface-buffalo_s": "buffalo_s",
    }.get(model_version)


def _embedding_to_bytes(embedding: list[float]) -> bytes:
    return json.dumps(embedding, separators=(",", ":")).encode("utf-8")


def _embedding_from_bytes(payload: bytes) -> list[float]:
    return [float(item) for item in json.loads(payload.decode("utf-8"))]


def _dot(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def _score_bucket(score: float) -> str:
    if score >= 0.75:
        return "very_high"
    if score >= 0.5:
        return "high"
    if score >= 0.25:
        return "medium"
    if score >= 0.0:
        return "low"
    return "negative"


def _liveness_policy(
    liveness: dict[str, Any] | None,
    require_liveness: bool,
) -> dict[str, object]:
    return {
        "type": "passive-quality-v1" if liveness else "none",
        "required": require_liveness,
        "verdict": _liveness_verdict(liveness),
    }


def _liveness_verdict(liveness: dict[str, Any] | None) -> str:
    if not liveness:
        return "not-applicable"
    verdict = liveness.get("verdict")
    return str(verdict) if verdict else "unknown"
