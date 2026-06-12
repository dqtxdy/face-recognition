"""Local simulator for the TrustFaceChain smart contract.

The simulator mirrors the Solidity contract's state transitions so the Python
demo and tests can run before a local EVM toolchain is installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time


class ContractError(RuntimeError):
    pass


class AlreadyEnrolled(ContractError):
    pass


class NotEnrolled(ContractError):
    pass


class Revoked(ContractError):
    pass


class EmptyValue(ContractError):
    pass


class NotAuthorized(ContractError):
    pass


@dataclass
class IdentityRecord:
    template_commitment: str
    consent_hash: str
    model_version: str
    enrolled: bool
    revoked: bool
    enrolled_at: int
    revoked_at: int


@dataclass(frozen=True)
class ChainEvent:
    event_type: str
    subject_id: str
    payload: dict[str, object]
    timestamp: int


class TrustFaceChainSimulator:
    def __init__(self, *, owner: str = "owner"):
        if not owner:
            raise EmptyValue("owner is required")
        self.owner = owner
        self.operators: dict[str, bool] = {owner: True}
        self.identities: dict[str, IdentityRecord] = {}
        self.events: list[ChainEvent] = []

    def set_operator(
        self,
        *,
        caller: str = "owner",
        operator: str,
        approved: bool,
    ) -> None:
        if caller != self.owner:
            raise NotAuthorized(caller)
        if not operator:
            raise EmptyValue("operator is required")
        self.operators[operator] = approved
        self._event(
            "OperatorUpdated",
            operator,
            {
                "approved": approved,
            },
        )

    def enroll_identity(
        self,
        *,
        caller: str = "owner",
        subject_id: str,
        template_commitment: str,
        consent_hash: str,
        model_version: str,
    ) -> None:
        self._require_operator(caller)
        if not subject_id or not template_commitment:
            raise EmptyValue("subject_id and template_commitment are required")
        existing = self.identities.get(subject_id)
        if existing and existing.enrolled and not existing.revoked:
            raise AlreadyEnrolled(subject_id)

        now = _now()
        self.identities[subject_id] = IdentityRecord(
            template_commitment=template_commitment,
            consent_hash=consent_hash,
            model_version=model_version,
            enrolled=True,
            revoked=False,
            enrolled_at=now,
            revoked_at=0,
        )
        self._event(
            "IdentityEnrolled",
            subject_id,
            {
                "templateCommitment": template_commitment,
                "consentHash": consent_hash,
                "modelVersion": model_version,
            },
        )

    def log_verification(
        self,
        *,
        caller: str = "owner",
        subject_id: str,
        verification_hash: str,
        model_version: str,
        accepted: bool,
    ) -> None:
        self._require_operator(caller)
        record = self.identities.get(subject_id)
        if not record or not record.enrolled:
            raise NotEnrolled(subject_id)
        if record.revoked:
            raise Revoked(subject_id)
        if not verification_hash:
            raise EmptyValue("verification_hash is required")
        self._event(
            "VerificationLogged",
            subject_id,
            {
                "verificationHash": verification_hash,
                "modelVersion": model_version,
                "accepted": accepted,
            },
        )

    def revoke_template(
        self,
        *,
        caller: str = "owner",
        subject_id: str,
        reason_hash: str,
    ) -> None:
        self._require_operator(caller)
        record = self.identities.get(subject_id)
        if not record or not record.enrolled:
            raise NotEnrolled(subject_id)
        if record.revoked:
            raise Revoked(subject_id)
        record.revoked = True
        record.revoked_at = _now()
        self._event(
            "TemplateRevoked",
            subject_id,
            {
                "reasonHash": reason_hash,
            },
        )

    def is_revoked(self, subject_id: str) -> bool:
        record = self.identities.get(subject_id)
        return bool(record and record.revoked)

    def _require_operator(self, caller: str) -> None:
        if caller != self.owner and not self.operators.get(caller, False):
            raise NotAuthorized(caller)

    def _event(self, event_type: str, subject_id: str, payload: dict[str, object]) -> None:
        self.events.append(
            ChainEvent(
                event_type=event_type,
                subject_id=subject_id,
                payload=payload,
                timestamp=_now(),
            )
        )


def _now() -> int:
    return int(time())
