# Strict Product Scorecard

Last updated: 2026-06-12

This document is the manager view. It separates demo progress from evidence
that would survive a serious technical defense or pilot conversation.

## Hard Decisions

### 1. Streamlit Is Not The Product UI

Decision: Streamlit remains a research and lab console only.

Reason:

- It is fast for experiments and reports.
- It is not the right surface for a buyer-facing product.
- It does not communicate production intent the way a dedicated web app does.

Current action:

- React/Vite pilot console added under `web/`.
- Product UI talks to the FastAPI service.
- Streamlit remains useful for internal benchmark viewing.

### 2. Dataset Evidence Is Better, But Not Final

Decision: smoke benchmarks are not acceptable as final evidence. The new
120-pair deep defense sample is good classroom evidence, but not the final
scientific claim.

Current evidence:

- Synthetic benchmark demo.
- Tiny official LFW-pairs smoke runs.
- Deep smoke on 20 balanced LFW pairs.
- Full official 6000-pair LFW classical baseline.
- Deep ArcFace defense sample on 120 balanced LFW pairs.

What this proves:

- The pipeline runs.
- Metrics export works.
- Deep adapters can execute locally.
- ArcFace-family models strongly outperform the classical baselines on the
  sampled LFW protocol.

What this does not prove:

- Model superiority.
- Robustness across age, pose, lighting, camera quality, or demographics.
- Production readiness.

### 3. Blockchain Is A Trust Layer, Not A Face Database

Decision: no raw images, crops, or plain embeddings go on-chain.

Acceptable on-chain or ledger-like data:

- template commitments,
- consent hashes,
- model versions,
- verification event hashes,
- revocation status.

Rejected:

- raw face images,
- aligned face crops,
- plain embeddings,
- recoverable biometric templates.

## Dataset Gates

| Gate | Minimum Requirement | Status |
| --- | --- | --- |
| Pipeline smoke | 20-40 pairs, deterministic and deep paths | Passed |
| LFW classical baseline | Full official LFW 6000-pair protocol | Passed |
| LFW deep defense sample | 120 balanced LFW pairs, Buffalo-S and Buffalo-L | Passed |
| LFW deep full protocol | Full official LFW 6000-pair protocol | Not done |
| Harder public tests | CALFW/CPLFW or XQLFW protocol | CSV adapter added, runs not done |
| Consent demo set | 10-20 consenting users, 20-40 images each | Not done |
| Robustness | brightness, blur, JPEG, occlusion, downscale | Demo path passed |
| Latency | Total embedding time measured for deep sample | Partial |
| Failure analysis | false accepts, false rejects, no-face cases | Not done |

## Model Gates

| Model | Role | Required Evidence |
| --- | --- | --- |
| Pixel/DCT/LBP/Eigenfaces | Classical baselines | Show why deep models are necessary |
| InsightFace Buffalo-S | Fast deep model | Accuracy, latency, robustness |
| InsightFace Buffalo-L | Strong deep model | Accuracy, latency, robustness |
| FaceNet or AdaFace/MagFace | Third serious model | Add if time allows |

Minimum final claim:

- At least three model families in the report.
- At least two real deep models in the working benchmark path.
- No claims based only on synthetic data or 20-pair smoke tests.
- Classical full-LFW results can be used as weak baselines, not as the headline.

## Product Gates

| Area | Gate | Status |
| --- | --- | --- |
| API | Enroll, verify, revoke, audit, metrics | Passed |
| Privacy | Raw image not persisted, encrypted embeddings | Passed prototype gate |
| Auth | API key for `/v1/*` endpoints | Passed prototype gate |
| Browser | CORS for local React console | Passed prototype gate |
| UI | React pilot console | Added |
| Liveness | Passive image quality/PAD gate | Passed prototype gate |
| Tenant safety | Tenant isolation and roles | Not done |
| Blockchain | Local EVM deployment, operator auth, gas report, JSON-RPC read | Passed |
| Compliance | Dataset card, model card, privacy review | Cards added, privacy review pending |

## Current 20/10 Verdict

Capstone readiness: close to 20/10 if the defense is honest about scope.

Product readiness: not sellable yet. The next blockers are tenant roles, full
deep benchmarks, harder datasets, trained PAD, and live JSON-RPC dashboard
transaction integration.

## Final Defense Standard

The final presentation should not say:

> Our model achieved high accuracy on LFW.

It should say:

> We built a privacy-preserving biometric verification system where face
> matching stays off-chain, biometric templates are encrypted, audit events are
> tamper-evident, revocation is enforced, and model behavior is evaluated across
> accuracy, latency, and robustness protocols.

That is the difference between a class demo and a serious product thesis.
