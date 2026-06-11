# Capstone Blueprint

## Project Name

TrustFaceChain: Privacy-Preserving Blockchain-Based Face Verification

## One-Sentence Pitch

TrustFaceChain verifies a person's face using modern deep embeddings while using
blockchain only for consent, auditability, versioned identity commitments, and
template revocation.

## Capstone Thesis

The impressive part is not only model accuracy. The impressive part is showing
that a biometric identity system can be:

- accurate under real-world conditions,
- measurable using professional biometric metrics,
- auditable through a blockchain ledger,
- privacy-aware by design,
- revocable when a template is compromised,
- explainable enough for a class demo and defense.

## Core Rule

Never store raw faces or plain face embeddings on-chain.

On-chain data should be limited to hashes, commitments, consent state, model
version identifiers, verification logs, and revocation records.

## Main Deliverables

1. Face verification pipeline
   - Detect face.
   - Align and crop face.
   - Generate embedding.
   - Compare embeddings with calibrated threshold.

2. Multi-model benchmark
   - FaceNet baseline.
   - ArcFace main model.
   - AdaFace or MagFace quality-aware model.
   - MobileFaceNet efficiency model.

3. Blockchain trust layer
   - Enroll identity commitment.
   - Register consent.
   - Log verification event.
   - Revoke compromised templates.
   - Track model version used for each verification.

4. Privacy and security layer
   - Salted template commitment.
   - Encrypted off-chain template store.
   - Revocable/cancelable template transform.
   - Threat model and mitigations.

5. Evaluation report
   - Accuracy, FAR/FMR, FRR/FNMR, EER.
   - ROC and DET curves.
   - TAR at fixed FAR.
   - Latency per model.
   - Memory and model size.
   - Blockchain gas/latency.
   - Robustness under blur, compression, lighting, pose, and occlusion.

6. Demo dashboard
   - Enrollment.
   - Verification.
   - Audit trail.
   - Revocation.
   - Model comparison.

## Why The Old Plan Was Too Small

The old plan was a conventional computer vision project:

- LFW dataset.
- Preprocessing.
- CNN/ResNet.
- FAR/FRR/EER.

That satisfies the basics, but it leaves three capstone-level questions
unanswered:

- What happens when image quality is bad?
- What happens if a biometric template leaks?
- Why is this a blockchain project instead of a normal database project?

TrustFaceChain answers all three.

## Success Criteria

Minimum excellent version:

- Three models benchmarked under one evaluation protocol.
- LFW plus at least one harder benchmark such as CALFW or XQLFW.
- Working smart contract with enroll, verify-log, and revoke flows.
- No raw image or plain embedding on-chain.
- Demo UI that clearly shows enrollment, verification, audit, and revocation.

World-class version:

- Four models, including MobileFaceNet and AdaFace/MagFace.
- LFW, CALFW, XQLFW, and synthetic robustness suite.
- Liveness or anti-spoofing check.
- Dashboard with ROC curves, threshold slider, and failure-case gallery.
- DID/VC-inspired identity model.
- Defense-ready threat model and privacy argument.

