# Roadmap And Defense

## Semester Roadmap

### Week 1: Foundation

- Freeze project scope.
- Set up repository structure.
- Implement dataset download instructions.
- Define consent policy for local demo data.
- Finalize model list.

### Week 2: Face Processing

- Add face detector.
- Add alignment pipeline.
- Save normalized crops for benchmark reproducibility.
- Verify pipeline on sample LFW images.

### Week 3: Model Interface

- Implement common embedder interface.
- Add FaceNet.
- Add ArcFace.
- Add AdaFace or MagFace.

### Week 4: Benchmark Runner

- Implement LFW pair evaluation.
- Compute accuracy, FAR/FMR, FRR/FNMR, and EER.
- Export CSV metrics.
- Plot ROC curve.

### Week 5: Robustness

- Add CALFW or XQLFW.
- Add synthetic corruption suite.
- Generate robustness report.

### Week 6: Efficiency

- Add MobileFaceNet.
- Measure latency and model size.
- Compare accuracy vs speed tradeoffs.

### Week 7: Blockchain

- Implement smart contract.
- Add local chain deployment.
- Add enroll, verify-log, and revoke flows.
- Add gas report.

### Week 8: Privacy Layer

- Add encrypted template store.
- Add salted commitments.
- Add consent record hashing.
- Add revocation checks before verification.

### Week 9: Demo App

- Build enrollment view.
- Build verification view.
- Build audit trail view.
- Build model comparison view.

### Week 10: Liveness And Threat Model

- Add simple liveness challenge or anti-spoofing module.
- Write threat model.
- Add failure gallery.

### Week 11: Report

- Write methodology.
- Add benchmark charts.
- Add blockchain/privacy explanation.
- Add limitations.

### Week 12: Defense Polish

- Rehearse 5-minute demo.
- Prepare Q&A.
- Confirm all scripts run from clean setup.

## Demo Story

1. Open dashboard.
2. Select model.
3. Enroll a user with explicit consent.
4. Show encrypted/off-chain template commitment.
5. Show blockchain enrollment event.
6. Verify the same person.
7. Show similarity score and decision.
8. Show blockchain audit event.
9. Try a wrong person or wrong image.
10. Revoke the template.
11. Show future verification blocked by revocation.
12. Show model comparison dashboard.

## Defense Angles

### Why blockchain?

Because biometric verification needs auditability, consent history, model
version accountability, and revocation. A normal database can be edited silently;
a blockchain event log makes identity operations tamper-evident.

### Why not put embeddings on-chain?

Because biometric templates are sensitive. If leaked, a face cannot be changed
like a password. The correct design is off-chain encrypted storage plus on-chain
commitments and revocation state.

### Why multiple models?

Because accuracy alone is not enough. ArcFace may be highly accurate, MobileFaceNet
may be faster, and quality-aware models may behave better under degraded images.
The project compares real deployment tradeoffs.

### Why LFW is not enough?

Modern face models can perform extremely well on LFW. Harder tests like CALFW
and XQLFW expose age, quality, and resolution sensitivity that a single LFW
score hides.

### What is the main limitation?

The project is a capstone prototype, not a production biometric system. It still
needs larger-scale testing, stronger anti-spoofing, formal privacy analysis, and
external security review before real deployment.

## Final Presentation Structure

1. Problem: biometric systems are accurate but privacy-dangerous.
2. Idea: keep matching off-chain, put accountability on-chain.
3. Architecture: face pipeline, privacy store, smart contract.
4. Models: FaceNet, ArcFace, AdaFace/MagFace, MobileFaceNet.
5. Evaluation: metrics, datasets, robustness, latency.
6. Demo: enroll, verify, audit, revoke.
7. Security: threat model and mitigations.
8. Results: best accuracy, best latency, best robustness.
9. Limitations and future work.

