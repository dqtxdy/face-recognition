# Dataset Card

System: TrustFaceChain evaluation package.

Last updated: 2026-06-12

## Dataset Sources

| Dataset | Status | Use |
| --- | --- | --- |
| Synthetic face-like arrays | Built in | Pipeline smoke tests |
| LFW via scikit-learn | Cached locally | Baseline and defense benchmarks |
| LFW official pairs | Cached locally | Verification protocol |
| Consent-based class set | Not collected | Live demo and pilot evidence |
| CALFW/CPLFW/XQLFW | Not loaded yet | Harder public benchmark gate |

## LFW Use

LFW is used because it is public, familiar, and easy to reproduce through the
current Python stack.

Current artifacts:

- `reports/lfw_full_classical_metrics.csv`
- `reports/lfw_full_classical_report.json`
- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`

Completed:

- Full official 6000-pair LFW classical baseline.
- 120-pair balanced LFW deep defense sample.

Not completed:

- Full 6000-pair LFW deep benchmark.
- Cross-age, cross-pose, or low-quality public protocols.

## Synthetic Data Use

Synthetic face-like arrays are used only to prove that benchmark, robustness,
CSV export, and metric plumbing work without heavy dependencies.

Synthetic results must not be presented as biometric accuracy.

## Consent Dataset Plan

For a class demo set:

- collect only from volunteers,
- explain purpose and retention,
- allow opt-out and deletion,
- store images outside git,
- record consent as JSON and hash it,
- avoid public release unless every participant explicitly agrees.

Recommended shape:

```text
data/faces/
  participant-001/
    image-001.jpg
    image-002.jpg
  participant-002/
    image-001.jpg
    image-002.jpg
```

Run:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-folder data/faces \
  --models pixel,dct,lbp,eigenfaces \
  --pairs-per-identity 2 \
  --csv reports/consent_metrics.csv \
  --json reports/consent_report.json
```

## Hard Public Benchmark Adapter

For CALFW, CPLFW, XQLFW, or any explicit-pair dataset, create a CSV:

```csv
left_path,right_path,label,left_identity,right_identity
data/calfw/A/1.jpg,data/calfw/A/2.jpg,1,A,A
data/calfw/A/1.jpg,data/calfw/B/1.jpg,0,A,B
```

Required columns:

- `left_path`
- `right_path`
- `label`

Optional columns:

- `left_identity`
- `right_identity`

Run:

```bash
PYTHONPATH=src python3 -m trustfacechain.cli benchmark-pairs-csv data/hard_pairs.csv \
  --models pixel,dct,lbp,eigenfaces \
  --csv reports/hard_pairs_metrics.csv \
  --json reports/hard_pairs_report.json
```

Or:

```bash
make hard-benchmark PAIRS_CSV=data/hard_pairs.csv
```

For deep models:

```bash
PYTHONPATH=vendor/face:src python3 -m trustfacechain.cli benchmark-pairs-csv data/hard_pairs.csv \
  --models arcface,mobileface \
  --csv reports/hard_pairs_deep_metrics.csv \
  --json reports/hard_pairs_deep_report.json
```

## Bias And Coverage Risks

Known risks:

- LFW is an older web-photo dataset.
- It does not represent every demographic or deployment camera.
- Public face datasets may contain consent and representation concerns.
- A class consent set will be too small for broad accuracy claims.
- Better benchmarks are needed for age, pose, lighting, and image quality.

## What We Can Claim

Allowed:

- The benchmark harness supports official LFW pairs and explicit pair CSVs.
- Classical baselines are weak on full LFW.
- ArcFace-family models perform strongly on the sampled LFW defense protocol.
- The system exports FAR, FRR, EER-style evidence.

Not allowed:

- Production accuracy.
- Demographic fairness.
- Spoof resistance.
- State-of-the-art performance.
- Generalization to all cameras and environments.

## Data Handling Rules

- Do not commit raw participant images.
- Do not commit private consent records with personal data.
- Store only hashes, reports, and anonymized metrics in the repository.
- Delete opt-out data immediately.
- Keep model and dataset limitations visible in the final presentation.
