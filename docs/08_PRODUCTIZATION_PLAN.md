# Productization Plan

## Product Positioning

TrustFaceChain is a privacy-first biometric verification layer for organizations
that need identity assurance with auditability and revocation.

The product is not "face recognition on blockchain." The product is:

> A biometric verification API that keeps biometric matching private while
> making consent, model versions, template state, and verification events
> tamper-evident.

## First Buyers

Best first markets:

- university labs and exam proctoring pilots,
- coworking spaces and restricted room access,
- internal enterprise attendance/check-in systems,
- security training demos for blockchain and biometrics,
- hackathon/event identity verification.

Avoid as first markets:

- government identity,
- border control,
- law enforcement,
- medical identity,
- large-scale public surveillance.

Those require stronger legal, ethical, and security maturity than a first
commercial pilot can responsibly claim.

## Paid Pilot Offer

Pilot package:

- API deployment for one controlled environment.
- Enrollment and verification dashboard.
- Audit export.
- Revocation flow.
- Model comparison report.
- Privacy/security briefing.
- One month of technical support.

Pilot success metrics:

- verification latency below target threshold,
- enrollment completion rate,
- false rejection rate under real lighting,
- audit event completeness,
- successful revocation test,
- operator satisfaction.

## Product Tiers

### Research Edition

- local SQLite persistence,
- local chain simulator,
- LFW benchmark tools,
- Streamlit demo dashboard.

### Pilot Edition

- API server deployment,
- encrypted template store,
- Ethereum testnet/local EVM adapter,
- admin dashboard,
- audit export,
- model and threshold configuration.

### Enterprise Edition

- HSM/KMS-backed keys,
- permissioned blockchain option,
- SSO and role-based access control,
- liveness/PAD module,
- compliance reporting,
- SLA monitoring,
- external security review.

## Differentiators

- Template revocation is treated as a first-class feature.
- No raw images or plain embeddings are written to the trust ledger.
- Model version is attached to every enrollment and verification event.
- Evaluation includes robustness and latency, not just accuracy.
- The API can be deployed without exposing model internals to client apps.
- Passive image quality/PAD checks can be enforced for image enroll and verify
  requests.

## Hard Product Truths

- Face recognition is sensitive and regulated in many regions.
- The system must never be sold as surveillance tooling.
- A real production launch still needs trained liveness/PAD, external security
  review, stronger key management, and legal review.
- The strongest commercial wedge is controlled, consent-based verification.

## Next Product Milestones

1. Run full deep LFW plus CALFW/CPLFW/XQLFW benchmarks.
2. Add trained liveness/PAD or active challenge checks.
3. Wire the React console to live JSON-RPC contract events.
4. Add role-based API keys and tenant isolation.
5. Add exportable audit reports.
6. Add admin dashboard views for tenants, models, and thresholds.
