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

The Streamlit dashboard is the current primary demo surface. The static HTML
prototype remains in `app/index.html` as a visual reference.

## Product API

```bash
make api
```

Default URL:

```text
http://127.0.0.1:8080
```

Optional API key mode:

```bash
TRUSTFACECHAIN_API_KEY=dev-secret make api
```

Then include `X-TrustFace-Key: dev-secret` on every `/v1/*` request. The
health endpoint remains open for uptime checks.

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
```

Output:

- `reports/lfw_deep_smoke_metrics.csv`
- `reports/lfw_deep_smoke_report.json`
