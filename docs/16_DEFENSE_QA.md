# Defense Q&A

Use this as rehearsal material. Answers should be short, direct, and honest.

## Is this really a blockchain project?

Yes. The blockchain is not used for face matching. It is used for the trust
layer: consent hash, template commitment, model version, verification event
hash, operator accountability, and revocation state.

## Why not store the face embedding on-chain?

Face embeddings are biometric data. If leaked, they cannot be rotated like a
password. TrustFaceChain stores encrypted embeddings off-chain and only stores
non-reversible commitments on-chain.

## What does the smart contract enforce?

The contract enforces owner/operator authorization, enrollment state, revocation
state, and audit events. Unauthorized callers cannot enroll, log verification,
or revoke templates.

## How do you prove the contract works?

`make chain-live` deploys the contract to Anvil, approves an operator, proves an
unauthorized write is blocked, enrolls, logs verification, revokes, and reads
revocation state. Evidence is written to:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`

## Why are the classical model results weak?

They are intentionally included as baselines. Pixel, DCT, LBP, and Eigenfaces
show why modern deep embeddings are necessary for unconstrained face
verification.

## Can you claim state-of-the-art accuracy?

No. The project can claim a working evaluation harness, full classical LFW
baseline, and strong sampled ArcFace defense evidence. Full deep LFW and harder
datasets are still needed for stronger scientific claims.

## Why use LFW if it is old?

LFW is public, familiar, and reproducible. It is a good starting point for a
capstone, but not enough by itself. The project now supports explicit pair CSVs
so CALFW, CPLFW, XQLFW, or consent data can be added.

## What is PAD in this project?

PAD means presentation attack detection. The current implementation is a
passive image quality gate that checks resolution, exposure, contrast, edge
energy, and texture signal. It is useful, but it is not a certified trained
anti-spoofing model.

## Does the system store raw images?

No. The product service decodes image bytes for inference, stores encrypted
embeddings, and records commitments and hashes. The consent payload explicitly
marks raw image storage as `none`.

## What happens after revocation?

The API blocks verification with HTTP `423`, the local simulator raises a
revocation error, and the Solidity contract records the revoked state.

## What is the biggest product risk?

Biometrics are sensitive and regulated. A production version needs trained PAD,
tenant isolation, role-based access, key management, monitoring, and legal
review.

## What is the strongest part of the project?

It treats face recognition as a complete trust workflow: evaluation, privacy,
authorization, auditability, revocation, and a real product console.

## What should you build next?

1. Full 6000-pair LFW deep benchmark.
2. CALFW/CPLFW/XQLFW benchmark CSVs.
3. Tenant roles and operator audit.
4. Trained PAD or active challenge.
5. Live JSON-RPC transaction flow from the dashboard.
