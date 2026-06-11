"""Small cryptographic helpers for hashes and commitments.

These helpers intentionally avoid storing or returning biometric vectors. They
only create deterministic commitments and hashes over already-protected data.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def random_hex(num_bytes: int = 32) -> str:
    return secrets.token_hex(num_bytes)


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def canonical_json_hash(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(payload))


def hmac_sha256_hex(key: bytes, message: bytes) -> str:
    return hmac.new(key, message, hashlib.sha256).hexdigest()

