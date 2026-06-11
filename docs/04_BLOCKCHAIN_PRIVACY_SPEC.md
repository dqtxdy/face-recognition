# Blockchain Privacy Spec

## Design Goal

Use blockchain to make biometric verification accountable without turning the
blockchain into a biometric leak.

## Privacy Rules

1. Raw face images never go on-chain.
2. Aligned face crops never go on-chain.
3. Plain embeddings never go on-chain.
4. Decryption keys never go on-chain.
5. Public events must not reveal direct real-world identity.
6. Every template must be revocable.
7. Every verification event must be linked to a model version.

## Identity Model

Use a pseudonymous subject id:

```text
subjectId = hash(userDID || appSalt)
```

The user-facing app can display a friendly name, but the contract should use
the pseudonymous id.

## Template Commitment

Baseline:

```text
templateCommitment = hash(protectedTemplate || templateSalt || modelVersion)
```

The protected template is stored off-chain in encrypted form.

Stretch:

- random projection / cancelable transform before storage,
- fuzzy vault or fuzzy extractor style key binding,
- encrypted-domain matching experiment.

## Consent Record

Consent should be represented as a signed JSON object:

```json
{
  "subjectId": "0x...",
  "purpose": "Face verification capstone demo",
  "scope": ["enrollment", "verification", "audit"],
  "expiresAt": "2026-12-31T23:59:59Z",
  "modelVersion": "arcface-r100-v1",
  "templateStorage": "encrypted-off-chain",
  "rawImageStorage": "none"
}
```

Store only `hash(consentRecord)` on-chain.

## Smart Contract Responsibilities

The contract should:

- register subject commitments,
- reject duplicate active enrollment unless explicitly updated,
- store consent hash,
- store active/revoked template state,
- emit events for enrollment, verification, update, and revocation,
- expose read functions for audit checks.

The contract should not:

- run face matching,
- store templates,
- store user names,
- store raw scores unless intentionally hashed or bucketed.

## Events

```solidity
event IdentityEnrolled(
    bytes32 indexed subjectId,
    bytes32 templateCommitment,
    bytes32 modelVersion,
    bytes32 consentHash
);

event VerificationLogged(
    bytes32 indexed subjectId,
    bytes32 verificationHash,
    bytes32 modelVersion,
    bool accepted
);

event TemplateRevoked(
    bytes32 indexed subjectId,
    bytes32 reasonHash
);
```

## Threat Model

### Threat: Raw biometric leak

Mitigation:

- no raw image persistence by default,
- no raw image on-chain,
- encrypted template storage only.

### Threat: Template theft

Mitigation:

- salt and transform templates,
- encrypt off-chain templates,
- allow revocation and re-enrollment.

### Threat: Replay attack

Mitigation:

- liveness challenge,
- signed nonce during verification,
- timestamped verification event hash.

### Threat: Model/version confusion

Mitigation:

- every enrollment and verification logs model version,
- benchmark reports separate metrics by model.

### Threat: Blockchain privacy leakage

Mitigation:

- pseudonymous ids,
- no raw scores by default,
- no personal labels in contract events.

## Defense Line

The system treats biometric data as hazardous. Blockchain is used for integrity
and accountability, not public biometric storage.

