# Runbook

This is the practical command sheet for the current prototype.

## Core Checks

```bash
make test
make smoke
```

`make test` runs unit tests. `make smoke` runs the original dependency-free
metric smoke test.

## Benchmark Demo

```bash
make benchmark-demo
```

Outputs:

- `reports/demo_metrics.csv`
- `reports/demo_report.json`

This benchmark uses synthetic face-like arrays. It tests the benchmark pipeline,
not real biometric performance.

## LFW Smoke Benchmark

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-lfw \
  --max-samples 40 \
  --pairs-per-identity 1 \
  --models pixel,dct \
  --csv reports/lfw_smoke_metrics.csv \
  --json reports/lfw_smoke_report.json
```

The first run downloads LFW into `data/cache/scikit_learn`.

The current `lfw_smoke` report is intentionally tiny. It proves the loader and
benchmark path work. It is not a final result.

## LFW Official Pairs Smoke

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-lfw-pairs \
  --max-pairs 20 \
  --models pixel,dct \
  --csv reports/lfw_pairs_smoke_metrics.csv \
  --json reports/lfw_pairs_smoke_report.json
```

When `--max-pairs` is used, the loader returns a balanced subset by default.
Use `--unbalanced` only when deliberately reproducing the raw beginning of
`pairs.txt`.

## LFW Full Classical Baseline

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-lfw-pairs \
  --models pixel,dct,lbp,eigenfaces \
  --csv reports/lfw_full_classical_metrics.csv \
  --json reports/lfw_full_classical_report.json
```

This runs the full official 6000-pair LFW protocol for the lightweight baseline
stack. The current result confirms that classical baselines are weak and should
be presented as justification for deep architectures, not as the final model.

## LFW Deep Defense Sample

```bash
make deep-defense
```

Default size is 120 balanced official LFW pairs. Override it with:

```bash
DEEP_PAIRS=300 make deep-defense
```

Outputs:

- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`

Current 120-pair results:

- `insightface-buffalo_l`: accuracy `1.0000`, EER `0.0000`,
  embedding time `128.60s`.
- `insightface-buffalo_s`: accuracy `1.0000`, EER `0.0000`,
  embedding time `57.36s`.

This is defense evidence, not the final scientific endpoint. For the strongest
claim, run the full 6000-pair protocol and add CALFW/CPLFW/XQLFW.

## Explicit Pair CSV Benchmark

Use this for CALFW, CPLFW, XQLFW, or a consent-pair protocol:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-pairs-csv data/hard_pairs.csv \
  --models pixel,dct,lbp,eigenfaces \
  --csv reports/hard_pairs_metrics.csv \
  --json reports/hard_pairs_report.json
```

Required CSV columns:

- `left_path`
- `right_path`
- `label`

Optional CSV columns:

- `left_identity`
- `right_identity`

Make shortcut:

```bash
make hard-benchmark PAIRS_CSV=data/hard_pairs.csv
```

Deep model example:

```bash
PYTHONPATH=vendor/face:src python3 -m trustfacechain.cli benchmark-pairs-csv data/hard_pairs.csv \
  --models arcface,mobileface \
  --csv reports/hard_pairs_deep_metrics.csv \
  --json reports/hard_pairs_deep_report.json
```

## Folder Benchmark

Use this when the group has a local consent-based demo dataset:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-folder data/faces \
  --models pixel,dct,lbp,eigenfaces \
  --pairs-per-identity 2 \
  --csv reports/folder_metrics.csv \
  --json reports/folder_report.json
```

Expected folder shape:

```text
data/faces/
  alice/
    image-001.jpg
    image-002.jpg
  bob/
    image-001.jpg
    image-002.jpg
```

## Chain Simulation

```bash
make chain-demo
```

This runs:

1. enroll identity,
2. log accepted verification,
3. revoke template,
4. prove future verification is blocked.

## Solidity Compile

```bash
make contracts-compile
```

Output:

- `contracts/TrustFaceChain.abi.json`
- `build/contracts/TrustFaceChain.json`

## Local EVM Deployment And Gas

Start Anvil:

```bash
/home/respectthanh/.foundry/bin/anvil --host 0.0.0.0 --port 8545
```

In another shell:

```bash
make chain-live
```

Outputs:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`

The live proof deploys the contract, delegates an operator, verifies that an
unauthorized writer is blocked, enrolls, logs verification, revokes, and reads
revocation state. Current gas values are:

- deploy: `582692`
- set operator: `45748`
- enroll identity: `141120`
- log verification: `40381`
- revoke template: `53588`

Note: `npm audit` currently reports `tmp` vulnerabilities through `solc`.
The suggested audit fix downgrades `solc` to an old major version, so do not
apply it blindly. Treat `solc` as a local dev-tool dependency and revisit this
when moving to a Hardhat/Foundry deployment stack.

## Robustness Demo

```bash
make robustness-demo
```

Output:

- `reports/robustness_demo.csv`

The current robustness demo uses synthetic face-like data. Its value is the
reporting path and corruption methodology. For final results, run the same suite
against LFW/CALFW/XQLFW or the consent-based class dataset.

## Dashboard

```bash
make demo-app
```

Then open:

```text
http://127.0.0.1:8501
```

The Streamlit dashboard is the research surface for benchmark inspection. The
static HTML prototype remains in `app/index.html` as a visual reference.

## React Pilot Console

```bash
make web
```

Default URL:

```text
http://127.0.0.1:5173
```

Use a non-default API URL:

```bash
VITE_TRUSTFACECHAIN_API_URL=http://127.0.0.1:18080 make web
```

Or pass it in the browser URL:

```text
http://127.0.0.1:5173/?apiUrl=http://127.0.0.1:18080
```

Use live-chain read mode after `make chain-live` or a known Anvil deployment:

```text
http://127.0.0.1:5173/?apiUrl=http://127.0.0.1:18080&rpcUrl=http://127.0.0.1:8545&contractAddress=0x5fbdb2315678afecb367f032d93f642f64180aa3
```

The chain panel calls `isRevoked(bytes32)` through JSON-RPC. It does not submit
transactions or handle private keys in the browser.

Build check:

```bash
make build-web
```

The React console is the product-facing pilot surface. It talks to the FastAPI
service for enrollment, verification, revocation, audit, and metrics. Streamlit
remains the research dashboard for benchmark inspection.

## Product API

```bash
make api
```

Default URL:

```text
http://127.0.0.1:8080
```

Use another API port:

```bash
make api API_PORT=18080
```

Optional API key mode:

```bash
TRUSTFACECHAIN_API_KEY=dev-secret make api
```

Then include `X-TrustFace-Key: dev-secret` on every `/v1/*` request. The
health endpoint remains open for uptime checks.

Browser access:

The API allows local React dev and preview origins by default:

- `http://127.0.0.1:5173`
- `http://localhost:5173`
- `http://127.0.0.1:5174`
- `http://localhost:5174`
- `http://127.0.0.1:5175`
- `http://localhost:5175`
- `http://127.0.0.1:4173`
- `http://localhost:4173`

Set `TRUSTFACECHAIN_CORS_ORIGINS` to override this comma-separated allowlist.

Smoke-tested HTTP flow:

1. `GET /health`
2. `POST /v1/enroll`
3. `POST /v1/verify`
4. `GET /v1/metrics`
5. `POST /v1/revoke`
6. `GET /v1/audit`
7. `POST /v1/verify` returns HTTP `423` after revocation.

Enrollment and verification accept exactly one biometric payload:

- `biometric_input` for the lightweight deterministic text demo.
- `image_base64` for PNG/JPEG image input.

Use `demo-image-hash-v1` for dependency-free image API tests. Use
`insightface-buffalo_l` or `insightface-buffalo_s` for optional deep image
inference after installing the InsightFace dependencies and model packs. Raw
image bytes are decoded for inference and are not persisted.

For image enroll or verify requests, set `"require_liveness": true` to enforce
the passive quality/PAD gate. The response includes a `liveness` report when an
image payload is analyzed.

Full endpoint examples are in `docs/API_REFERENCE.md`.

## Deployment Assets

- `requirements.txt`
- `Dockerfile`
- `.dockerignore`
- `scripts/export-openapi.py`

The Docker image starts the API on port `8080`. Optional InsightFace model packs
are intentionally excluded from the image by default because they are large and
should be handled as deployment artifacts.

## Deep Model Adapters

Adapter slots exist for:

- ArcFace via InsightFace,
- FaceNet via facenet-pytorch,
- MobileFaceNet via ONNXRuntime.

They are optional until the heavier dependencies and model weights are installed.

ArcFace/InsightFace is currently installed under `vendor/face` in this workspace.
Run ArcFace commands with:

```bash
make deep-smoke
make deep-defense
```

Output:

- `reports/lfw_deep_smoke_metrics.csv`
- `reports/lfw_deep_smoke_report.json`
- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`
