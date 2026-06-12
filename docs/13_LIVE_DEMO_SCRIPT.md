# Live Demo Script

Purpose: run a controlled 8 to 10 minute demo without improvising under
pressure.

## Pre-Demo Setup

Terminal 1: API

```bash
make api API_PORT=18081
```

Terminal 2: React console

```bash
make web
```

Open:

```text
http://127.0.0.1:5173/?apiUrl=http%3A%2F%2F127.0.0.1%3A18081
```

Optional terminal 3: Anvil

```bash
/home/respectthanh/.foundry/bin/anvil --host 0.0.0.0 --port 8545
```

Optional terminal 4: live-chain proof

```bash
make chain-live
```

Use this console URL when Anvil is running:

```text
http://127.0.0.1:5173/?apiUrl=http%3A%2F%2F127.0.0.1%3A18081&rpcUrl=http%3A%2F%2F127.0.0.1%3A8545&contractAddress=0x5fbdb2315678afecb367f032d93f642f64180aa3
```

## Timing

### 0:00 to 0:45 - Thesis

Say:

TrustFaceChain is not putting face recognition on-chain. Matching stays
off-chain. Blockchain stores the accountability layer: consent hash, template
commitment, model version, audit event, and revocation status.

Show:

- React console.
- Pipeline strip: Capture, Embed, Encrypt, Commit.

### 0:45 to 2:00 - Enroll

Action:

- Keep model on `Image Hash` for fast demo.
- Keep subject as `subject-pilot-001`.
- Click `Enroll`.

Say:

The API stores an encrypted reference embedding and returns public-safe hashes.
No raw image bytes are persisted.

Show:

- Metrics count increases.
- Audit table receives `IdentityEnrolled`.

### 2:00 to 3:00 - Verify

Action:

- Click `Verify`.

Say:

Verification compares the probe to the stored encrypted reference. The audit log
does not store the full score as a sensitive biometric trace. It stores a
verification hash and coarse score bucket.

Show:

- Accepted or rejected result.
- Audit table receives `VerificationLogged`.

### 3:00 to 4:00 - Passive PAD Gate

Action:

- Turn on `PAD gate`.
- Click `Verify` again.

Say:

The passive PAD gate checks capture quality signals before matching. It is not a
certified anti-spoofing model, but it prevents obvious low-quality or unsafe
captures from silently entering the biometric flow.

Show:

- PAD state changes to `Pass` or `Review`.

### 4:00 to 5:00 - Revoke

Action:

- Click `Revoke`.
- Click `Verify` again.

Say:

Revocation is first-class. After revocation, the API returns HTTP `423` and the
subject cannot be verified until re-enrolled.

Show:

- Revoked count increases.
- Result shows verification blocked.

### 5:00 to 6:15 - Blockchain Proof

Action:

- If Anvil is running, click `Check chain`.
- Open `reports/local_chain_report.json`.
- Open `reports/local_chain_gas.csv`.

Say:

The live local EVM proof deploys the contract, approves an operator, blocks an
unauthorized writer, enrolls, logs verification, revokes, and reads revocation
state. This is not just a Solidity file. It was executed.

Show:

- `unauthorizedWriteBlocked: true`.
- `revoked: true`.
- Gas values.

### 6:15 to 7:30 - Evaluation Evidence

Open:

- `reports/lfw_full_classical_metrics.csv`
- `reports/lfw_deep_defense_metrics.csv`
- `reports/robustness_demo.csv`

Say:

The classical models are weak on the full LFW protocol, which justifies the
deep-learning direction. The sampled ArcFace defense benchmark gives stronger
evidence, and the robustness suite shows how we evaluate quality beyond
accuracy.

### 7:30 to 8:30 - Limitations

Say:

The full 6000-pair deep LFW protocol and harder datasets like CALFW, CPLFW, or
XQLFW are still needed before making scientific claims. A production launch
would also need trained PAD, tenant roles, stronger key management, and legal
review.

### 8:30 to 9:00 - Close

Say:

This is a blockchain capstone because blockchain adds accountability to a
sensitive biometric workflow. It gives the system consent evidence, audit
integrity, model-version traceability, and revocation.

## Fallbacks

If React fails:

```bash
make check
```

Then show API docs and reports.

If Anvil fails:

Show:

- `reports/local_chain_report.json`
- `reports/local_chain_gas.csv`
- [contracts/TrustFaceChain.sol](../contracts/TrustFaceChain.sol)

Say:

The local EVM proof was run before the defense and the report contains the
transaction hashes and gas values.

If deep models are too slow:

Show:

- `reports/lfw_deep_defense_metrics.csv`
- `reports/lfw_deep_defense_report.json`

Say:

The deep run is reproducible with `make deep-defense`, but we do not run it live
because CPU inference takes several minutes.

## Do Not Say

- "This is production-ready."
- "This detects all spoofing attacks."
- "We achieved final state-of-the-art accuracy."
- "Blockchain stores the face."

## Say Instead

- "This is a capstone-grade privacy and accountability prototype."
- "The passive PAD gate catches low-quality captures, not all attacks."
- "The sampled deep benchmark is strong defense evidence, not the final science
  endpoint."
- "The blockchain stores commitments and audit state, not biometric data."
