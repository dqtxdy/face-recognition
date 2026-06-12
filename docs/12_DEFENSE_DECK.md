# Defense Deck

Purpose: 8 to 10 minute capstone defense. Keep the slides visual and sparse.
Use this file as the speaker plan and source of truth.

## Slide 1: TrustFaceChain

Headline: Privacy-preserving face verification with blockchain accountability.

Visual: React console first screen.

Speaker point:

TrustFaceChain does not put face images on-chain. Face matching stays off-chain.
The blockchain records consent, commitments, model version, audit events, and
revocation state.

## Slide 2: Problem

Headline: Face verification has an accountability gap.

Bullets:

- A face cannot be rotated like a password.
- Operators need consent and audit proof.
- Model and threshold changes affect real decisions.
- Revocation is often treated as an afterthought.

Speaker point:

The project is about accountable biometric operations, not just recognizing a
face in a webcam demo.

## Slide 3: Architecture

Headline: Match privately. Prove publicly.

Visual: Capture -> Embed -> Encrypt -> Commit.

Bullets:

- API accepts one biometric payload.
- Embedding is encrypted off-chain.
- Commitment and consent hash are audit-safe.
- Verification logs include model version and event hash.
- Revocation blocks later verification.

Speaker point:

The trust boundary is explicit. Biometric material is treated as hazardous and
kept away from the ledger.

## Slide 4: Blockchain Design

Headline: Blockchain is the trust layer.

Bullets:

- On-chain: commitments, consent hash, model version, revocation state.
- Off-chain: raw image, face crop, embedding, encryption key.
- Owner/operator authorization protects writes.
- Local EVM proof produces transaction hashes and gas usage.

Evidence:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`

Speaker point:

An attacker cannot write enrollment, verification, or revocation events unless
they are the owner or an approved operator.

## Slide 5: Models

Headline: Baselines explain why deep architectures matter.

Bullets:

- Classical models: Pixel, DCT, LBP, Eigenfaces.
- Deep models: InsightFace Buffalo-S and Buffalo-L.
- Deterministic hash path is for API smoke tests only.

Evidence:

- Classical full LFW baseline: weak, around 55-62 percent accuracy.
- ArcFace 120-pair LFW sample: Buffalo-S and Buffalo-L both reached 1.0000
  accuracy and 0.0000 EER.

Speaker point:

The classical stack is deliberately included so we can show the gap between
simple feature engineering and modern deep embeddings.

## Slide 6: Evaluation

Headline: Accuracy is not enough.

Bullets:

- FAR, FRR, EER.
- Threshold selection.
- Latency and embedding time.
- Robustness checks: brightness, blur, JPEG, occlusion, downscale.
- Failure analysis is the next full-science gate.

Evidence:

- `reports/lfw_full_classical_metrics.csv`
- `reports/lfw_deep_defense_metrics.csv`
- `reports/robustness_demo.csv`

Speaker point:

We present metric evidence, not a single screenshot or a single success case.

## Slide 7: Product API

Headline: The system behaves like a product surface.

Bullets:

- Enroll.
- Verify.
- Revoke.
- Identity metadata.
- Audit.
- Metrics.
- Optional API key for `/v1/*`.

Demo:

Use the React console. Show an enrollment, verification, audit event, and
revocation.

Speaker point:

Streamlit is the lab. React plus FastAPI is the product-facing path.

## Slide 8: Passive PAD Gate

Headline: Low-quality captures are blocked before matching.

Bullets:

- Checks resolution, exposure, contrast, edge energy, and texture signal.
- Optional `require_liveness` enforcement for image enroll and verify.
- Returns a structured report.
- Not a certified anti-spoofing model.

Speaker point:

This is a prototype safety gate. We are honest that a production launch still
needs trained PAD or an active challenge.

## Slide 9: Honest Limitations

Headline: We know where the boundary is.

Bullets:

- Full 6000-pair LFW deep run is still needed.
- CALFW/CPLFW/XQLFW should be added for harder public testing.
- Tenant isolation and role-based operators are still needed.
- Trained PAD and compliance review are required before real deployment.
- `solc` dev dependency has a documented audit caveat.

Speaker point:

The project is serious because it does not pretend a prototype is a finished
biometric platform.

## Slide 10: Closing

Headline: A blockchain capstone with a real product thesis.

Final line:

TrustFaceChain proves that biometric verification can be private by design,
auditable by default, and revocable when trust changes.

Speaker point:

The result is not just face recognition. It is a privacy and accountability
system around face recognition.
