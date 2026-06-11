# Product Language

This file adapts the local `SKILL.md` for TrustFaceChain. The skill is written
for landing pages and portfolios, but this project is a technical security/ML
demo. Use the taste rules, not the page template assumptions.

## Design Read

TrustFaceChain is a capstone-grade biometric security system for teachers,
classmates, and technical evaluators. It should feel rigorous, calm, and
credible. It should not feel like a crypto hype page or an AI image-generation
landing page.

## Dials

- DESIGN_VARIANCE: 5
- MOTION_INTENSITY: 3
- VISUAL_DENSITY: 6

Rationale:

- The system needs enough visual polish to impress.
- It also needs enough density to show metrics, contracts, and audit events.
- Motion should support comprehension, not perform for attention.

## Visual Principles

1. Dashboard first
   - The first screen should be the working product, not a marketing hero.
   - Primary views: Enroll, Verify, Audit, Models, Evaluation.

2. Trust over spectacle
   - Avoid neon crypto visuals.
   - Avoid generic purple-blue AI gradients.
   - Use restrained contrast, clear hierarchy, and readable metrics.

3. One accent color
   - Suggested accent: emerald or cyan.
   - Use it for active states, verified status, and focused controls.
   - Do not mix multiple status palettes beyond necessary semantic colors.

4. Clear states
   - Enrollment pending.
   - Consent signed.
   - Template committed.
   - Verification accepted/rejected.
   - Template revoked.
   - Chain transaction pending/confirmed/failed.

5. No fake certainty
   - Show thresholds and scores.
   - Show model version.
   - Show why a decision happened.
   - Show failures honestly.

## Layout Guidance

Use an application layout:

- left navigation rail,
- top status bar,
- main work surface,
- right-side context panel when needed.

Recommended routes:

- `/enroll`
- `/verify`
- `/audit`
- `/models`
- `/evaluation`
- `/settings`

## Component Language

### Enrollment Card

Use a single focused work panel:

- camera/image input,
- detected face preview,
- consent summary,
- selected model,
- enroll action,
- chain status.

### Verification Panel

Show:

- probe image,
- reference identity,
- similarity score,
- threshold,
- decision,
- model version,
- revocation status.

### Audit Trail

Use a dense but readable table:

- event type,
- subject id,
- model version,
- transaction hash,
- timestamp,
- status.

### Model Comparison

Use charts and metric tiles:

- EER,
- TAR at FAR,
- p95 latency,
- model size,
- robustness drop.

## Copy Rules

Use plain technical language:

- "Enroll identity"
- "Verify face"
- "Revoke template"
- "Audit event"
- "Model version"
- "Template commitment"

Avoid vague marketing copy:

- "AI-powered identity revolution"
- "Unlock the future"
- "Seamless next-gen trust"
- "Military-grade" unless formally justified.

## Motion Rules

Allowed:

- subtle row highlight on new audit event,
- pending transaction progress,
- score meter transition,
- camera capture feedback.

Avoid:

- looping abstract backgrounds,
- floating orbs,
- crypto coin animations,
- excessive glass panels.

## Accessibility Rules

- High text contrast.
- Labels above inputs.
- No placeholder-as-label.
- Keyboard-accessible flows.
- Clear accepted/rejected status beyond color alone.
- Responsive layout that preserves the primary workflow on laptop screens.

## Pre-Flight Check

Before presenting the UI:

- Can a teacher understand the core flow in 30 seconds?
- Can a classmate see the blockchain value without reading the report?
- Is every biometric privacy risk explicitly handled?
- Are model metrics visible, not hidden in a notebook?
- Does the UI look like a serious system rather than a template?

