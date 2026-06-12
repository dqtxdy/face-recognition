# Current Status

Last updated: 2026-06-12

## Working Now

### Core Python Package

- `trustfacechain.metrics`: FAR/FRR/EER-style verification metrics.
- `trustfacechain.datasets`: synthetic data, folder datasets, LFW loader, and
  official LFW pairs loader.
- `trustfacechain.benchmark`: multi-model benchmark runner.
- `trustfacechain.robustness`: corruption sensitivity suite.
- `trustfacechain.templates`: first-pass protected-template commitments.
- `trustfacechain.chain_sim`: local smart-contract behavior simulator.
- `trustfacechain.liveness`: passive image quality gate for low-quality capture
  and presentation-attack risk signals.

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

- Solidity contract with owner/operator authorization.
- ABI JSON.
- Python simulator with tests.
- Enroll, verification-log, revoke, and revoke-block behavior.
- Local Anvil deployment proof.
- Gas report export.
- Unauthorized write attempt blocked on the live local EVM.

Not yet done:

- Live JSON-RPC connection from dashboard.

### Dashboard

Working:

- Streamlit app at `app/streamlit_app.py`.
- React pilot console at `web/`.
- Enrollment simulation.
- Verification simulation.
- Audit event table.
- Template revocation.
- Benchmark report display.
- Robustness report display.

Clarification:

- Streamlit is the research dashboard.
- React is the product-facing pilot console.

### Product API

Working:

- FastAPI app at `trustfacechain.api`.
- Persistent SQLite store.
- Encrypted reference embedding storage.
- Text and base64 image biometric payload support.
- Dependency-free `demo-image-hash-v1` image path for API testing.
- Optional InsightFace image inference path for `insightface-buffalo_l` and
  `insightface-buffalo_s`.
- Passive image quality/PAD gate with optional enforcement for image payloads.
- Enrollment endpoint.
- Verification endpoint.
- Revocation endpoint.
- Identity metadata endpoint.
- Audit endpoint.
- Metrics endpoint.
- OpenAPI export.
- Optional `X-TrustFace-Key` API-key protection for `/v1/*` endpoints.
- CORS allowlist for the local React console.

Current API caveat:

- The default API model remains deterministic for fast local tests. Real image
  inference is available through optional InsightFace model versions.
- The passive liveness gate catches low-quality captures, but it is not a full
  trained anti-spoofing model.

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
make build-web
make check
make chain-live
make deep-defense
```

All passed in the current workspace. `make chain-live` requires a running Anvil
node on `127.0.0.1:8545`.

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

The deeper ArcFace defense sample also passed:

```bash
make deep-defense
```

Outputs:

- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`

Current 120-pair balanced LFW deep defense results:

- `insightface-buffalo_l`: accuracy `1.0000`, EER `0.0000`,
  embedding time `128.60s`.
- `insightface-buffalo_s`: accuracy `1.0000`, EER `0.0000`,
  embedding time `57.36s`.

Manager interpretation: this is strong defense evidence beyond smoke, but it is
still a sampled LFW run. The full 6000-pair deep run and harder datasets remain
the scientific finish line.

The full official LFW protocol passed for the classical baseline stack:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-lfw-pairs \
  --models pixel,dct,lbp,eigenfaces \
  --csv reports/lfw_full_classical_metrics.csv \
  --json reports/lfw_full_classical_report.json
```

Outputs:

- `reports/lfw_full_classical_metrics.csv`
- `reports/lfw_full_classical_report.json`

Current 6000-pair LFW classical results:

- `pixel-cosine`: accuracy `0.6167`, EER `0.3897`.
- `dct-low-frequency`: accuracy `0.5983`, EER `0.4133`.
- `lbp-histogram`: accuracy `0.5532`, EER `0.4623`.
- `eigenfaces-pca`: accuracy `0.6180`, EER `0.3887`.

Manager interpretation: these are baselines, not competitive biometric models.
They justify the deep-model track rather than replacing it.

The Solidity compile path passed:

```bash
make contracts-compile
```

Compiler output:

- `contracts/TrustFaceChain.abi.json`
- `build/contracts/TrustFaceChain.json`

The live local EVM route passed:

```bash
make chain-live
```

Outputs:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`

Current gas results:

- deploy: `582692`
- set operator: `45748`
- enroll identity: `141120`
- log verification: `40381`
- revoke template: `53588`

The report confirms `unauthorizedWriteBlocked: true` and `revoked: true`.

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
- The current benchmark reports include a 120-pair ArcFace defense sample, but
  final biometric claims still need the full LFW deep protocol and harder
  datasets.
- The lightweight recognizers are baselines and engineering scaffolds, not the
  final deep-learning claim.
- The full 6000-pair LFW run has been completed for classical baselines only.
  Deep full-protocol runs are still needed for final model claims.
- The passive liveness gate is a quality/PAD prototype, not a certified
  anti-spoofing model.
- Final capstone results should still add FaceNet and AdaFace/MagFace if time
  allows.

## Next Technical Milestones

1. Run full 6000-pair LFW deep benchmarks for Buffalo-S and Buffalo-L.
2. Add CALFW/CPLFW/XQLFW support.
3. Add tenant isolation and role-based API keys.
4. Add a trained liveness/PAD model or active challenge.
5. Wire the React console to live JSON-RPC contract events.
6. Add exportable pilot reports.
