# Security And Privacy Posture

## Security Claim

TrustFaceChain is privacy-preserving by architecture because it separates:

- biometric matching,
- biometric template storage,
- consent/audit records,
- blockchain accountability.

The trust ledger receives commitments and event hashes, not raw biometric
material.

## Data Classification

### Highly Sensitive

- raw face images,
- aligned face crops,
- face embeddings,
- liveness captures,
- encryption keys.

### Sensitive

- subject ids,
- template commitments,
- consent hashes,
- verification decisions,
- model versions,
- audit events.

### Public-Safe Demo Data

- benchmark metrics,
- aggregate counts,
- model names,
- public documentation.

## Current Controls

- Encrypted local reference embedding storage in the API prototype.
- Template commitments rather than plain template publication.
- Consent hashing.
- Revocation state.
- Audit events.
- Model version attached to enrollment and verification.
- API responses avoid returning encrypted embeddings.
- Raw image payloads are decoded for inference and are not persisted.
- Optional API-key protection for `/v1/*` endpoints.

## Required Controls Before A Real Pilot

- Role-based API keys or operator authentication.
- Operator authorization and role separation.
- Transport TLS.
- KMS or HSM key storage.
- Rate limiting.
- Structured security logs.
- Liveness or presentation-attack detection.
- Tenant isolation.
- Data retention policy.
- Backup and recovery policy.

## Required Controls Before Production

- External penetration test.
- Biometric privacy legal review.
- DPIA or equivalent privacy assessment where required.
- Bias/demographic evaluation.
- Presentation attack detection evaluation.
- Incident response playbook.
- Secure key rotation.
- Disaster recovery tests.

Completed capstone documentation:

- Formal model card.
- Formal dataset card.

## Threat Model

### Template Theft

Risk:

An attacker obtains stored biometric templates.

Current mitigation:

- encrypted local embedding storage,
- template commitments,
- revocation flow.

Future mitigation:

- KMS-backed encryption,
- cancelable template transforms,
- fuzzy extractor or key-binding scheme,
- hardware-backed keys.

### Replay Attack

Risk:

An attacker reuses a previous face capture or API request.

Current mitigation:

- audit event hashing,
- revocation checks.
- passive image quality/PAD gate for image requests.

Future mitigation:

- signed challenge nonce,
- trained liveness/PAD or active challenge,
- timestamp windows,
- request signing.

### Ledger Privacy Leakage

Risk:

Public audit records reveal too much about identities or verification behavior.

Current mitigation:

- subject ids are pseudonymous,
- raw biometric data is not stored on-chain,
- event payloads use hashes/commitments.

Future mitigation:

- tenant-specific salts,
- zero-knowledge proof experiments,
- private data collections or permissioned ledger mode.

### Model Drift

Risk:

Changing the model silently changes verification behavior.

Current mitigation:

- model version stored per identity and event.

Future mitigation:

- model registry,
- signed model artifacts,
- threshold migration reports.

## Ethical Use Policy

TrustFaceChain should be used only for:

- consent-based verification,
- controlled access,
- opt-in attendance/check-in,
- education and research,
- security auditing demonstrations.

TrustFaceChain should not be used for:

- covert surveillance,
- public face search,
- law-enforcement watchlists,
- emotion or personality inference,
- identity decisions without human appeal.
