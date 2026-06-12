# API Reference

TrustFaceChain exposes a product-style API for enrollment, verification,
revocation, audit, and operational metrics.

Run locally:

```bash
make api
```

Default URL:

```text
http://127.0.0.1:8080
```

If port `8080` is occupied during local demos, run Uvicorn manually on another
port and set the React console API URL field to that address.

Optional API key protection:

```bash
TRUSTFACECHAIN_API_KEY=dev-secret make api
```

When configured, every `/v1/*` endpoint requires:

```text
X-TrustFace-Key: dev-secret
```

`/health` stays unauthenticated for uptime checks.

Local browser origins allowed by default:

- `http://127.0.0.1:5173`
- `http://localhost:5173`
- `http://127.0.0.1:5174`
- `http://localhost:5174`
- `http://127.0.0.1:5175`
- `http://localhost:5175`
- `http://127.0.0.1:4173`
- `http://localhost:4173`

Set `TRUSTFACECHAIN_CORS_ORIGINS` to override the comma-separated allowlist.

Export OpenAPI:

```bash
make api-openapi
```

Output:

```text
build/openapi/trustfacechain.openapi.json
```

## Health

```bash
curl http://127.0.0.1:8080/health
```

Response:

```json
{
  "status": "ok",
  "service": "trustfacechain-api"
}
```

## Enroll

Provide exactly one biometric payload:

- `biometric_input`: lightweight text stand-in for development.
- `image_base64`: base64-encoded PNG/JPEG face image for image inference.
- `require_liveness`: optional image-only passive quality/PAD enforcement.

```bash
curl -X POST http://127.0.0.1:8080/v1/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "subject-demo-001",
    "biometric_input": "alice enrollment",
    "model_version": "demo-hash-v1",
    "consent": {
      "purpose": "pilot access control",
      "scope": ["enrollment", "verification", "audit"]
    }
  }'
```

Response:

```json
{
  "subjectId": "subject-demo-001",
  "modelVersion": "demo-hash-v1",
  "templateCommitment": "...",
  "consentHash": "...",
  "eventHash": "...",
  "liveness": null
}
```

Image enrollment uses the same endpoint:

```json
{
  "subject_id": "subject-demo-001",
  "image_base64": "<base64-png-or-jpeg>",
  "model_version": "demo-image-hash-v1",
  "require_liveness": true,
  "consent": {
    "purpose": "pilot access control",
    "scope": ["enrollment", "verification", "audit"]
  }
}
```

For optional deep inference, use `insightface-buffalo_l` or
`insightface-buffalo_s` as `model_version` after installing the optional
InsightFace dependencies and model packs. The API stores encrypted embeddings
and template commitments, not raw image bytes.

When an image payload is analyzed, the response includes a `liveness` object
with `passed`, `score`, `verdict`, and individual quality checks. This is a
passive quality gate, not a certified anti-spoofing model.

## Verify

```bash
curl -X POST http://127.0.0.1:8080/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "subject-demo-001",
    "biometric_input": "alice enrollment",
    "threshold": 0.62
  }'
```

Image verification:

```json
{
  "subject_id": "subject-demo-001",
  "image_base64": "<base64-png-or-jpeg>",
  "threshold": 0.62,
  "require_liveness": true
}
```

Response:

```json
{
  "subjectId": "subject-demo-001",
  "modelVersion": "demo-hash-v1",
  "score": 1.0,
  "threshold": 0.62,
  "accepted": true,
  "verificationHash": "...",
  "liveness": null
}
```

## Revoke

```bash
curl -X POST http://127.0.0.1:8080/v1/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "subject-demo-001",
    "reason": "user requested re-enrollment"
  }'
```

Response:

```json
{
  "subjectId": "subject-demo-001",
  "reasonHash": "...",
  "eventHash": "..."
}
```

After revocation, `/v1/verify` returns HTTP `423`.

## Identity

```bash
curl http://127.0.0.1:8080/v1/identities/subject-demo-001
```

Returns public identity metadata only. It does not return the encrypted
embedding or raw biometric material.

## Audit

```bash
curl "http://127.0.0.1:8080/v1/audit?subject_id=subject-demo-001&limit=20"
```

Returns ordered audit events with event hashes and non-sensitive payload fields.

## Metrics

```bash
curl http://127.0.0.1:8080/v1/metrics
```

Returns counts for identities, active identities, revoked identities, and audit
events.

## Error Codes

- `400`: invalid biometric payload or unsupported image model.
- `401`: missing or invalid API key when `TRUSTFACECHAIN_API_KEY` is set.
- `409`: active identity already enrolled.
- `422`: request validation failed or enforced passive liveness failed.
- `423`: identity revoked.
