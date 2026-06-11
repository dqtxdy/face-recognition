# TrustFaceChain

TrustFaceChain is a privacy-preserving face verification system that combines
modern deep face recognition with blockchain-backed consent, auditability, and
template revocation.

The project is designed for a blockchain capstone, but the core thesis is not
"put face recognition on-chain." The thesis is:

> Face matching should stay off-chain, while blockchain records the trust layer:
> consent, identity commitments, model versions, verification events, and
> revocation state.

## Why This Is Different

Typical capstone face-recognition projects stop at LFW accuracy and a webcam
demo. This project aims higher:

- At least three recognition models, including a historical baseline, a strong
  angular-margin model, and a quality-aware or mobile model.
- A NIST-style evaluation protocol with FMR/FNMR, FAR/FRR, EER, ROC/DET,
  latency, storage, memory, and robustness testing.
- A blockchain layer that never stores raw biometric images or plain face
  embeddings.
- A revocation mechanism for biometric templates.
- A trust-first demo UI that behaves like a serious security product, not a
  generic AI landing page.

## Planned Models

- FaceNet: triplet-loss embedding baseline.
- ArcFace: main high-accuracy angular-margin model.
- AdaFace or MagFace: quality-aware model for degraded inputs.
- MobileFaceNet: lightweight edge/mobile model.

## Planned Stack

- ML: Python, PyTorch, InsightFace-compatible model interfaces.
- Face detection/alignment: RetinaFace or MTCNN.
- Evaluation: reproducible benchmark runner and metrics reports.
- Blockchain: Ethereum local network with Solidity smart contracts, or
  Hyperledger Fabric if the course expects permissioned blockchain.
- Off-chain storage: encrypted local store first; optional IPFS CID references.
- App: trust-first web dashboard for enrollment, verification, audit, and model
  comparison.

## Repository Map

- [docs/01_CAPSTONE_BLUEPRINT.md](docs/01_CAPSTONE_BLUEPRINT.md): project thesis,
  deliverables, and success criteria.
- [docs/02_SYSTEM_ARCHITECTURE.md](docs/02_SYSTEM_ARCHITECTURE.md): components,
  trust boundaries, and data flow.
- [docs/03_MODEL_AND_EVALUATION_PLAN.md](docs/03_MODEL_AND_EVALUATION_PLAN.md):
  model lineup, datasets, metrics, and robustness tests.
- [docs/04_BLOCKCHAIN_PRIVACY_SPEC.md](docs/04_BLOCKCHAIN_PRIVACY_SPEC.md):
  smart contract responsibilities and privacy rules.
- [docs/05_ROADMAP_AND_DEFENSE.md](docs/05_ROADMAP_AND_DEFENSE.md): semester
  roadmap, demo story, and defense angles.
- [docs/06_RUNBOOK.md](docs/06_RUNBOOK.md): commands for tests, benchmarks,
  chain simulation, and dashboard.
- [docs/07_CURRENT_STATUS.md](docs/07_CURRENT_STATUS.md): current working
  state, caveats, and next milestones.
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md): product API endpoints and
  curl examples.
- [docs/08_PRODUCTIZATION_PLAN.md](docs/08_PRODUCTIZATION_PLAN.md): pilot,
  tiers, buyers, and product roadmap.
- [docs/09_SECURITY_AND_PRIVACY.md](docs/09_SECURITY_AND_PRIVACY.md): security
  posture, threat model, and ethical use policy.
- [docs/10_PILOT_PITCH.md](docs/10_PILOT_PITCH.md): buyer-facing pilot pitch.
- [docs/11_STRICT_PRODUCT_SCORECARD.md](docs/11_STRICT_PRODUCT_SCORECARD.md):
  manager-grade readiness gates and dataset standards.
- [docs/design/PRODUCT_LANGUAGE.md](docs/design/PRODUCT_LANGUAGE.md): visual
  direction for a non-sloppy, trust-first demo experience.

## Quick Start

Run the dependency-free core checks:

```bash
make test
make smoke
make benchmark-demo
make robustness-demo
make chain-demo
make contracts-compile
make api-openapi
npm run build:web
```

Run the optional deep-model smoke after InsightFace dependencies are available:

```bash
make deep-smoke
```

Hash the example consent record:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli hash-consent examples/consent.example.json
```

Create a public protected-template record from a small demo vector:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli protect-template \
  --subject-id subject-demo-001 \
  --model-version arcface-r100-v1 \
  --app-salt capstone-demo \
  --vector "0.2,-0.4,0.9,0.1"
```

Open the dashboard prototype directly in a browser:

```text
app/index.html
```

Run the interactive Streamlit dashboard:

```bash
make demo-app
```

Run the React pilot console:

```bash
make web
```

Run the product API:

```bash
make api
```

The default embedder is a deterministic smoke-test path, not a final biometric
claim. The API also supports base64 image payloads and optional InsightFace
image inference after the deep dependencies and model packs are installed.

## Current Implementation

- Python package in `src/trustfacechain`.
- Biometric metrics in `trustfacechain.metrics`.
- Product API in `trustfacechain.api`.
- SQLite persistence in `trustfacechain.store`.
- Enroll/verify/revoke service logic in `trustfacechain.product_service`.
- Starter template protection in `trustfacechain.templates`.
- Dependency-free mock embedder in `trustfacechain.models.hash_embedder`.
- Solidity contract draft in `contracts/TrustFaceChain.sol`.
- Static demo dashboard in `app/`.
- Interactive Streamlit dashboard in `app/streamlit_app.py`.
- React pilot console in `web/`.
- Optional InsightFace deep smoke reports in `reports/lfw_deep_smoke_metrics.csv`.
- Full official LFW classical baseline in `reports/lfw_full_classical_metrics.csv`.
- Deployment starter files: `Dockerfile`, `.dockerignore`, `requirements.txt`.
- Unit tests in `tests/`.

## References

- FaceNet: https://arxiv.org/abs/1503.03832
- ArcFace: https://arxiv.org/abs/1801.07698
- AdaFace: https://arxiv.org/abs/2204.00964
- MagFace: https://arxiv.org/abs/2103.06627
- MobileFaceNets: https://arxiv.org/abs/1804.07573
- RetinaFace: https://arxiv.org/abs/1905.00641
- CALFW: https://arxiv.org/abs/1708.08197
- XQLFW: https://arxiv.org/abs/2108.10290
- NIST FRTE 1:1: https://pages.nist.gov/frvt/html/frvt11.html
- W3C DID Core: https://www.w3.org/TR/did-core/
- W3C Verifiable Credentials 2.0: https://www.w3.org/TR/vc-data-model-2.0/
- IPFS CIDs: https://docs.ipfs.tech/concepts/content-addressing/
