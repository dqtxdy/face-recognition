# Model Card

System: TrustFaceChain face verification prototype.

Last updated: 2026-06-12

## Intended Use

TrustFaceChain supports consent-based identity verification demos where a user
enrolls voluntarily and later verifies against their own enrolled template.

The model stack is intended for:

- capstone evaluation,
- benchmark comparison,
- privacy-preserving workflow demonstration,
- controlled pilot exploration with human override.

It is not intended for:

- surveillance,
- watchlist search,
- criminal identification,
- covert biometric collection,
- fully automated high-stakes decisions.

## Model Lineup

| Model | Type | Role |
| --- | --- | --- |
| `pixel-cosine` | Classical baseline | Shows naive pixel matching limits |
| `dct-low-frequency` | Classical baseline | Frequency-domain baseline |
| `lbp-histogram` | Classical baseline | Texture baseline |
| `eigenfaces-pca` | Classical baseline | Historical face-recognition baseline |
| `insightface-buffalo_s` | Deep ArcFace-family model | Fast deep model |
| `insightface-buffalo_l` | Deep ArcFace-family model | Stronger deep model |
| `demo-hash-v1` | Deterministic test embedder | API smoke path only |
| `demo-image-hash-v1` | Deterministic image test embedder | Dependency-free image API path only |

The deterministic hash embedders are not biometric-performance models. They are
used for reproducible API and UI tests.

## Current Evidence

### Full Classical LFW Baseline

Protocol: official LFW 6000-pair protocol.

Report:

- `reports/lfw_full_classical_metrics.csv`
- `reports/lfw_full_classical_report.json`

Results:

| Model | Accuracy | EER |
| --- | ---: | ---: |
| `pixel-cosine` | 0.6167 | 0.3897 |
| `dct-low-frequency` | 0.5983 | 0.4133 |
| `lbp-histogram` | 0.5532 | 0.4623 |
| `eigenfaces-pca` | 0.6180 | 0.3887 |

Interpretation:

These baselines are weak. Their value is educational and comparative. They
justify using deep embeddings.

### Deep LFW Defense Sample

Protocol: 120 balanced official LFW pairs.

Report:

- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`

Results:

| Model | Accuracy | EER | Embedding Time |
| --- | ---: | ---: | ---: |
| `insightface-buffalo_l` | 1.0000 | 0.0000 | 128.60s |
| `insightface-buffalo_s` | 1.0000 | 0.0000 | 57.36s |

Interpretation:

This is strong capstone defense evidence. It is not a final scientific claim
because the full deep LFW protocol and harder public datasets are still needed.

## Thresholding

The benchmark runner selects the best threshold on the evaluated pairs and also
reports EER threshold. In a real deployment, thresholds must be chosen against
business risk:

- stricter threshold for high-security access,
- lower threshold only with human review,
- separate thresholds per model version after validation.

## Performance Notes

The current deep runs use CPU execution. Buffalo-S is materially faster than
Buffalo-L in the sampled benchmark. Production latency claims should be measured
on the target hardware with p50 and p95 values.

## Known Risks

- LFW is not representative of all identities, ages, lighting, devices, or
  deployment contexts.
- The 120-pair deep result is sampled evidence.
- Demographic fairness is not yet measured.
- The passive PAD gate is not a trained anti-spoofing model.
- Deep model dependencies and weights are optional local artifacts, not bundled
  into the default Docker image.

## Recommended Next Evaluation

1. Run full 6000-pair LFW deep protocol for Buffalo-S and Buffalo-L.
2. Add CALFW/CPLFW/XQLFW through `benchmark-pairs-csv`.
3. Add a consent-based class dataset with explicit opt-in.
4. Produce false-accept and false-reject examples for defense discussion.
5. Measure p50 and p95 latency per model on the demo laptop.

## Ethical Boundary

This model stack must be used only for opt-in verification. It should not be
presented as a surveillance or identification system.
