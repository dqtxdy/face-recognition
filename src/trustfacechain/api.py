"""FastAPI application for the product prototype."""

from __future__ import annotations

import os
from pathlib import Path
import secrets
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from trustfacechain.product_service import (
    IdentityAlreadyActive,
    IdentityNotFound,
    IdentityRevoked,
    InvalidBiometricInput,
    TrustFaceProductService,
    UnsupportedModelVersion,
    build_product_service,
)


class BiometricRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    subject_id: str = Field(min_length=1)
    biometric_input: str | None = Field(default=None, min_length=1)
    image_base64: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_single_biometric_payload(self) -> "BiometricRequest":
        has_text = bool(self.biometric_input and self.biometric_input.strip())
        has_image = bool(self.image_base64 and self.image_base64.strip())
        if has_text == has_image:
            raise ValueError("provide exactly one of biometric_input or image_base64")
        return self


class EnrollRequest(BiometricRequest):
    model_version: str = "demo-hash-v1"
    consent: dict[str, Any] = Field(default_factory=dict)
    allow_reenroll: bool = False


class VerifyRequest(BiometricRequest):
    threshold: float = Field(default=0.62, ge=-1.0, le=1.0)


class RevokeRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    subject_id: str = Field(min_length=1)
    reason: str = Field(default="user requested revocation", min_length=1)


def _api_key_guard(configured_api_key: str | None):
    async def guard(
        x_trustface_key: str | None = Header(default=None, alias="X-TrustFace-Key"),
    ) -> None:
        if not configured_api_key:
            return None
        if not x_trustface_key or not secrets.compare_digest(
            x_trustface_key,
            configured_api_key,
        ):
            raise HTTPException(status_code=401, detail="invalid API key")
        return None

    return guard


def create_app(
    *,
    service: TrustFaceProductService | None = None,
    db_path: str | Path = "data/runtime/trustfacechain.db",
    key_path: str | Path = "data/runtime/fernet.key",
    api_key: str | None = None,
) -> FastAPI:
    app = FastAPI(
        title="TrustFaceChain API",
        version="0.1.0",
        description=(
            "Privacy-preserving face verification API prototype. "
            "Face matching stays off-chain; commitments and audit events are tracked."
        ),
    )
    app.state.service = service or build_product_service(
        db_path=db_path,
        key_path=key_path,
    )
    configured_api_key = api_key if api_key is not None else os.environ.get(
        "TRUSTFACECHAIN_API_KEY"
    )
    require_api_key = Depends(_api_key_guard(configured_api_key))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "trustfacechain-api"}

    @app.post("/v1/enroll")
    async def enroll(
        request: EnrollRequest,
        _: None = require_api_key,
    ) -> dict[str, Any]:
        try:
            result = app.state.service.enroll(
                subject_id=request.subject_id,
                biometric_input=request.biometric_input,
                image_base64=request.image_base64,
                model_version=request.model_version,
                consent=request.consent,
                allow_reenroll=request.allow_reenroll,
            )
        except IdentityAlreadyActive as error:
            raise HTTPException(status_code=409, detail="identity already active") from error
        except (InvalidBiometricInput, UnsupportedModelVersion) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {
            "subjectId": result.subject_id,
            "modelVersion": result.model_version,
            "templateCommitment": result.template_commitment,
            "consentHash": result.consent_hash,
            "eventHash": result.event_hash,
        }

    @app.post("/v1/verify")
    async def verify(
        request: VerifyRequest,
        _: None = require_api_key,
    ) -> dict[str, Any]:
        try:
            result = app.state.service.verify(
                subject_id=request.subject_id,
                biometric_input=request.biometric_input,
                image_base64=request.image_base64,
                threshold=request.threshold,
            )
        except IdentityNotFound as error:
            raise HTTPException(status_code=404, detail="identity not found") from error
        except IdentityRevoked as error:
            raise HTTPException(status_code=423, detail="identity revoked") from error
        except (InvalidBiometricInput, UnsupportedModelVersion) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {
            "subjectId": result.subject_id,
            "modelVersion": result.model_version,
            "score": result.score,
            "threshold": result.threshold,
            "accepted": result.accepted,
            "verificationHash": result.verification_hash,
        }

    @app.post("/v1/revoke")
    async def revoke(
        request: RevokeRequest,
        _: None = require_api_key,
    ) -> dict[str, str]:
        try:
            result = app.state.service.revoke(
                subject_id=request.subject_id,
                reason=request.reason,
            )
        except IdentityNotFound as error:
            raise HTTPException(status_code=404, detail="identity not found") from error
        except IdentityRevoked as error:
            raise HTTPException(status_code=423, detail="identity revoked") from error
        return {
            "subjectId": result.subject_id,
            "reasonHash": result.reason_hash,
            "eventHash": result.event_hash,
        }

    @app.get("/v1/identities/{subject_id}")
    async def get_identity(
        subject_id: str,
        _: None = require_api_key,
    ) -> dict[str, Any]:
        identity = app.state.service.get_identity(subject_id)
        if not identity:
            raise HTTPException(status_code=404, detail="identity not found")
        return {
            "subjectId": identity.subject_id,
            "modelVersion": identity.model_version,
            "templateCommitment": identity.template_commitment,
            "consentHash": identity.consent_hash,
            "revoked": identity.revoked,
            "createdAt": identity.created_at,
            "updatedAt": identity.updated_at,
            "revokedAt": identity.revoked_at,
        }

    @app.get("/v1/audit")
    async def audit(
        subject_id: str | None = None,
        limit: int = Query(default=100, ge=1, le=1000),
        _: None = require_api_key,
    ) -> dict[str, list[dict[str, Any]]]:
        events = app.state.service.list_events(subject_id=subject_id, limit=limit)
        return {
            "events": [
                {
                    "eventId": event.event_id,
                    "eventType": event.event_type,
                    "subjectId": event.subject_id,
                    "payload": event.payload,
                    "createdAt": event.created_at,
                }
                for event in events
            ]
        }

    @app.get("/v1/metrics")
    async def metrics(_: None = require_api_key) -> dict[str, int]:
        return app.state.service.metrics()

    return app


app = create_app()
