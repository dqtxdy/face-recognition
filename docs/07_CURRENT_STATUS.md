# Current Status

Last updated: 2026-06-11

## Working Now

### Core Python Package

- `trustfacechain.metrics`: FAR/FRR/EER-style verification metrics.
- `trustfacechain.datasets`: synthetic data, folder datasets, LFW loader, and
  official LFW pairs loader.
- `trustfacechain.benchmark`: multi-model benchmark runner.
- `trustfacechain.robustness`: corruption sensitivity suite.
- `trustfacechain.templates`: first-pass protected-template commitments.
- `trustfacechain.chain_sim`: local smart-contract behavior simulator.

### Model Support

Runnable lightweight recognizers:

- `pixel-cosine`
- `dct-low-frequency`
- `lbp-histogram`
- `eigenfaces-pca`

Optional deep adapter slots:

- ArcFace through InsightFace.
- FaceNet through facenet-pytorch.
- MobileFaceNet through ONNXRuntime.

ArcFace/InsightFace dependencies and the `buffalo_l` and `buffalo_s` model packs
are installed locally under `vendor/face` and `data/cache/insightface`.

The attempted `buffalo_m` pack download completed, but the current
`FaceAnalysis` adapter cannot use it because the pack does not expose the
expected detection model. Treat `buffalo_m` as unsupported until a
recognition-only adapter is added.

FaceNet remains scaffolded but not installed with model weights. A standalone
MobileFaceNet ONNX adapter is scaffolded; the working lightweight deep path today
is InsightFace `buffalo_s`, whose recognition model is `w600k_mbf.onnx`.

### Blockchain Layer

Working:

- Solidity contract draft.
- ABI JSON.
- Python simulator with tests.
- Enroll, verification-log, revoke, and revoke-block behavior.

Not yet done:

- Hardhat/Foundry deployment.
- Gas report.
- Live JSON-RPC connection from dashboard.

### Dashboard

Working:

- Streamlit app at `app/streamlit_app.py`.
- Enrollment simulation.
- Verification simulation.
- Audit event table.
- Template revocation.
- Benchmark report display.
- Robustness report display.

### Product API

Working:

- FastAPI app at `trustfacechain.api`.
- Persistent SQLite store.
- Encrypted reference embedding storage.
- Text and base64 image biometric payload support.
- Dependency-free `demo-image-hash-v1` image path for API testing.
- Optional InsightFace image inference path for `insightface-buffalo_l` and
  `insightface-buffalo_s`.
- Enrollment endpoint.
- Verification endpoint.
- Revocation endpoint.
- Identity metadata endpoint.
- Audit endpoint.
- Metrics endpoint.
- OpenAPI export.
- Optional `X-TrustFace-Key` API-key protection for `/v1/*` endpoints.

Current API caveat:

- The default API model remains deterministic for fast local tests. Real image
  inference is available through optional InsightFace model versions, but final
  biometric results still require full-protocol benchmarks.

Run the dashboard with:

```bash
make demo-app
```

Current local URL:

```text
http://127.0.0.1:8501
```

Run the API with:

```bash
make api
```

Default API URL:

```text
http://127.0.0.1:8080
```

## Verified Commands

```bash
make test
make smoke
make benchmark-demo
make chain-demo
make robustness-demo
make contracts-compile
make api-openapi
make check
```

All passed in the current workspace.

The LFW dataset was downloaded into:

```text
data/cache/scikit_learn
```

The official-pairs smoke command also passed:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-lfw-pairs \
  --max-pairs 20 \
  --models pixel,dct \
  --csv reports/lfw_pairs_smoke_metrics.csv \
  --json reports/lfw_pairs_smoke_report.json
```

The optional deep-model smoke also passed:

```bash
make deep-smoke
```

Current deep smoke outputs:

- `reports/lfw_deep_smoke_metrics.csv`
- `reports/lfw_deep_smoke_report.json`

The Solidity compile path passed:

```bash
make contracts-compile
```

Compiler output:

- `contracts/TrustFaceChain.abi.json`
- `build/contracts/TrustFaceChain.json`

`npm audit` reports one high and one low issue through `solc`'s transitive
`tmp` dependency. The offered fix downgrades `solc` to an incompatible old major
version, so this is documented as a local dev-tool caveat.

The product API passed unit tests and a real HTTP smoke flow on port `8080`:

- health returned `200`,
- enrollment returned a template commitment,
- verification returned accepted,
- metrics returned identity and audit counts,
- revocation returned a reason hash,
- audit returned all three events,
- verification after revocation returned HTTP `423`.

OpenAPI export passed:

```bash
make api-openapi
```

Output:

- `build/openapi/trustfacechain.openapi.json`

## Important Caveats

- The current dashboard uses deterministic text embeddings as a stand-in for
  live face embeddings.
- The API now accepts image payloads, but the default dependency-free image
  model is still a deterministic demo path, not a biometric-performance claim.
- The current benchmark reports prove the pipeline, not final biometric
  performance.
- The lightweight recognizers are baselines and engineering scaffolds, not the
  final deep-learning claim.
- The deep smoke currently uses only 20 balanced official LFW pairs. Final
  results should use the full LFW protocol plus harder benchmarks.
- Final capstone results should still add FaceNet and AdaFace/MagFace if time
  allows.

## Next Technical Milestones

1. Replace dashboard text input with image upload inference.
2. Add liveness/PAD checks.
3. Add tenant isolation and role-based API keys.
4. Add CALFW/XQLFW support.
5. Deploy contract to a local EVM and produce gas metrics.
6. Add exportable pilot reports.
