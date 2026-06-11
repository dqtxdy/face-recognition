"""Template protection primitives for the first prototype."""

from __future__ import annotations

from dataclasses import dataclass

from trustfacechain.crypto import hmac_sha256_hex, random_hex, sha256_hex


@dataclass(frozen=True)
class ProtectedTemplate:
    subject_id: str
    model_version: str
    template_salt: str
    protected_vector: list[int]
    commitment: str

    def to_public_record(self) -> dict[str, object]:
        return {
            "subjectId": self.subject_id,
            "modelVersion": self.model_version,
            "templateSalt": self.template_salt,
            "templateCommitment": self.commitment,
            "protectedVectorLength": len(self.protected_vector),
        }


class TemplateProtector:
    """Creates a revocable, app-scoped binary template commitment.

    The first implementation is deliberately simple: binarize an embedding, then
    flip signs using an HMAC-derived mask. Re-enrollment with a new salt creates
    a different protected template for the same face embedding.
    """

    def __init__(self, app_salt: bytes):
        if not app_salt:
            raise ValueError("app_salt must not be empty")
        self.app_salt = app_salt

    def protect(
        self,
        *,
        subject_id: str,
        model_version: str,
        embedding: list[float],
        template_salt: str | None = None,
    ) -> ProtectedTemplate:
        if not embedding:
            raise ValueError("embedding must not be empty")
        salt = template_salt or random_hex(16)
        binary = [1 if value >= 0 else 0 for value in embedding]
        mask = self._mask(subject_id=subject_id, model_version=model_version, salt=salt)
        protected = [
            bit ^ (int(mask[index % len(mask)], 16) & 1)
            for index, bit in enumerate(binary)
        ]
        commitment = self._commitment(
            subject_id=subject_id,
            model_version=model_version,
            salt=salt,
            protected=protected,
        )
        return ProtectedTemplate(
            subject_id=subject_id,
            model_version=model_version,
            template_salt=salt,
            protected_vector=protected,
            commitment=commitment,
        )

    def _mask(self, *, subject_id: str, model_version: str, salt: str) -> str:
        message = f"{subject_id}:{model_version}:{salt}".encode("utf-8")
        return hmac_sha256_hex(self.app_salt, message)

    def _commitment(
        self,
        *,
        subject_id: str,
        model_version: str,
        salt: str,
        protected: list[int],
    ) -> str:
        payload = (
            f"{subject_id}:{model_version}:{salt}:"
            + "".join(str(item) for item in protected)
        )
        return sha256_hex(payload.encode("utf-8"))

