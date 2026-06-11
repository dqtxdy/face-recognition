# Model And Evaluation Plan

## Model Lineup

### Model 1: FaceNet

Role: historical baseline.

Why it matters:

- Popularized direct face embeddings with triplet loss.
- Easy to explain in class.
- Useful as a baseline against newer margin-loss systems.

### Model 2: ArcFace

Role: main high-accuracy model.

Why it matters:

- Additive angular margin loss gives a strong geometric explanation.
- Widely used in modern face-recognition systems.
- Strong default candidate for the main demo.

### Model 3: AdaFace or MagFace

Role: quality-aware model.

Why it matters:

- Real face systems fail under poor quality, blur, pose, low light, and
  compression.
- AdaFace and MagFace explicitly address quality or quality-related embedding
  behavior.

### Model 4: MobileFaceNet

Role: efficiency model.

Why it matters:

- Shows deployment thinking.
- Lets the team compare accuracy against latency and model size.
- Useful for webcam/mobile-style demo constraints.

## Datasets

### Required Baseline

- LFW: standard unconstrained face verification benchmark.

### Harder Benchmarks

- CALFW: cross-age variation.
- XQLFW: cross-quality and cross-resolution variation.
- Optional CFP-FP: frontal-profile pose variation.
- Optional AgeDB: age variation.

### Local Demo Dataset

Use a small consent-based class/group dataset only for the live demo, not as the
main scientific benchmark. Every participant should explicitly consent.

## Evaluation Tasks

### 1:1 Verification

Given two face images, decide whether they belong to the same identity.

Metrics:

- Accuracy.
- FAR/FMR.
- FRR/FNMR.
- EER.
- ROC curve.
- DET curve.
- TAR at fixed FAR.

### 1:N Identification

Optional stretch goal.

Given one probe face, search a gallery and return the most likely identity.

Metrics:

- Rank-1 accuracy.
- Rank-5 accuracy.
- Search latency.
- Gallery size sensitivity.

## Robustness Suite

Create controlled corruptions on evaluation images:

- Gaussian blur.
- Motion blur.
- JPEG compression.
- Brightness decrease.
- Brightness increase.
- Contrast shift.
- Gaussian noise.
- Synthetic occlusion over lower face.
- Downscale/upscale resolution loss.

Report performance drop per corruption level.

## Threshold Calibration

Each model needs:

- validation threshold selected on validation pairs,
- test metrics reported without re-tuning,
- threshold table for operating points.

Important operating points:

- low-friction mode: lower false rejection, higher false acceptance risk,
- secure mode: lower false acceptance, higher false rejection risk,
- balanced mode: near EER.

## Efficiency Metrics

Measure:

- detector latency,
- alignment latency,
- embedding latency,
- matching latency,
- end-to-end verification latency,
- model file size,
- peak memory,
- CPU vs GPU timing if available.

Report median, p95, and p99 when possible.

## Blockchain Metrics

Measure:

- enroll transaction gas,
- verification log transaction gas,
- revoke transaction gas,
- local chain transaction latency,
- event query latency,
- storage growth per enrolled identity.

## Output Artifacts

- `metrics.csv`: per-model benchmark summary.
- `roc_curves.png`: ROC plot.
- `det_curves.png`: DET plot.
- `latency_report.csv`: timing breakdown.
- `robustness_report.csv`: corruption sensitivity.
- `blockchain_costs.csv`: gas and transaction timing.
- `failure_gallery/`: false accepts and false rejects for defense discussion.

## Evaluation Claim To Defend

TrustFaceChain is not claiming to beat industrial vendors. It is claiming to
build a complete, measurable, privacy-aware biometric verification system with
professional evaluation discipline.

