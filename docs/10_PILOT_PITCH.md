# Pilot Pitch

## One-Liner

TrustFaceChain is a privacy-first face verification API with blockchain-backed
consent, auditability, and template revocation.

## The Problem

Organizations want fast biometric verification, but biometric systems create
three hard risks:

- face data cannot be changed like a password,
- operators need proof of consent and audit trails,
- model and threshold changes can silently affect decisions.

## The Solution

TrustFaceChain keeps face matching private and off-chain while recording the
trust layer:

- enrollment commitment,
- consent hash,
- model version,
- verification event hash,
- revocation state.

## Demo Flow

1. Enroll a subject through the API or dashboard.
2. Store an encrypted reference embedding locally.
3. Record a public-safe template commitment.
4. Verify the same subject.
5. Show score, threshold, and model version.
6. Show audit event.
7. Revoke the template.
8. Prove future verification is blocked.
9. Show passive PAD gate on an image payload.
10. Show local-chain gas report.
11. Show LFW deep-model defense sample.
12. Show robustness report.

## Why A Buyer Cares

- Consent is not a PDF lost in a folder; it is hashed and tied to identity
  state.
- Verification events are auditable.
- Compromised templates can be revoked and replaced.
- Model versions are visible.
- The system can be piloted without storing raw face images on-chain.

## Pilot Scope

Recommended first pilot:

- 20-100 consenting users,
- one physical or digital access workflow,
- one month,
- opt-in only,
- human override available,
- weekly audit export.

## Pilot Deliverables

- working API deployment,
- admin/demo dashboard,
- encrypted template store,
- enrollment and verification audit log,
- revocation drill,
- latency report,
- robustness report,
- final pilot readout.

## Pricing Hypothesis

For a student/startup pilot:

- setup fee: low fixed fee,
- monthly pilot support fee,
- optional custom integration fee.

For enterprise later:

- per-location platform fee,
- per-active-subject tier,
- premium security/compliance add-on.

## Honest Limitations

Current prototype limitations:

- The dashboard still uses deterministic text input as a stand-in for live
  camera embeddings.
- The API accepts base64 image payloads and can route to optional InsightFace
  inference, but final biometric claims still require full-protocol benchmarks.
- Passive image quality/PAD enforcement is implemented, but a trained
  anti-spoofing model or active challenge is still needed before production.
- API-key protection is implemented, but role-based access control and tenant
  isolation are still required for a serious pilot.
- Legal/compliance review is required before real biometric deployment.

This honesty is a strength in a defense or buyer conversation. It shows the team
understands the risk surface.
