# System Architecture

## High-Level Components

TrustFaceChain has five layers:

1. Capture layer
   - Webcam or uploaded image.
   - Optional liveness challenge.

2. Face processing layer
   - Face detection.
   - Landmark alignment.
   - Normalized crop generation.

3. Recognition layer
   - Model-specific embedding generation.
   - Similarity scoring.
   - Threshold decision.

4. Privacy and storage layer
   - Encrypted template storage.
   - Salted template commitments.
   - Optional IPFS CID references.

5. Blockchain trust layer
   - Identity enrollment commitments.
   - Consent records.
   - Verification audit logs.
   - Template revocation.
   - Model version registry.

## Main Data Flow

### Enrollment

1. User gives consent.
2. System captures or uploads face image.
3. Face detector finds ROI.
4. Aligner normalizes face crop.
5. Recognition model creates embedding.
6. Template protection module transforms and encrypts the template.
7. Off-chain storage saves encrypted template.
8. Blockchain stores:
   - user DID or generated identity id,
   - encrypted-template hash or CID,
   - model version id,
   - consent record hash,
   - revocation status.

### Verification

1. User presents face.
2. System performs detection and alignment.
3. Selected model creates probe embedding.
4. System retrieves encrypted reference template off-chain.
5. System decrypts or derives protected comparison form.
6. Matcher computes similarity score.
7. Threshold module returns accept/reject.
8. Blockchain logs:
   - verification id,
   - identity commitment,
   - model version,
   - decision hash,
   - timestamp,
   - operator/verifier id.

### Revocation

1. User or admin revokes template.
2. Smart contract marks template commitment as revoked.
3. Future verification rejects revoked templates.
4. User can re-enroll with a new salt/transform.

## Trust Boundaries

### Trusted

- Local ML inference runtime during demo.
- Contract code after deployment.
- User wallet/private key.

### Semi-Trusted

- Backend API.
- Off-chain encrypted storage.
- IPFS pinning service if used.

### Untrusted

- Raw network inputs.
- Uploaded images.
- External verifier requests.
- Any public blockchain observer.

## What Goes On-Chain

Allowed:

- Hashes and commitments.
- DID or pseudonymous identity id.
- Consent status.
- Model version id.
- Revocation flag.
- Verification event hash.
- Contract event logs.

Not allowed:

- Raw face images.
- Aligned face crops.
- Plain embeddings.
- Decryption keys.
- Plain personal information.

## Model Interface

All recognition models should implement the same interface:

```python
class FaceEmbedder:
    name: str
    version: str
    embedding_dim: int

    def preprocess(self, aligned_face):
        ...

    def embed(self, aligned_face):
        ...

    def score(self, embedding_a, embedding_b):
        ...
```

This lets the benchmark runner compare models without rewriting the pipeline.

## Contract Interface Draft

```solidity
function enrollIdentity(
    bytes32 subjectId,
    bytes32 templateCommitment,
    bytes32 consentHash,
    bytes32 modelVersion
) external;

function logVerification(
    bytes32 subjectId,
    bytes32 verificationHash,
    bytes32 modelVersion,
    bool accepted
) external;

function revokeTemplate(bytes32 subjectId, bytes32 reasonHash) external;

function isRevoked(bytes32 subjectId) external view returns (bool);
```

## Architectural Principle

The blockchain is not the face-recognition engine. It is the accountability
engine.

