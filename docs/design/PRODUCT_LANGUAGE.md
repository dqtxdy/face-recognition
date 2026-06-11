# Product Language

This file adapts the local `SKILL.md` for TrustFaceChain. The skill is written
for landing pages and portfolios, but this project is a technical security/ML
demo. Use the taste rules, not the page template assumptions.

## Design Read

TrustFaceChain is a capstone-grade biometric security system for teachers,
classmates, and technical evaluators. It should feel like a mission-critical
identity console: rigorous, calm, technical, and slightly uncommon. It should
not feel like a crypto hype page, an AI image-generation landing page, or a
default SaaS admin template.

## Dials

- DESIGN_VARIANCE: 7
- MOTION_INTENSITY: 3
- VISUAL_DENSITY: 7

Rationale:

- The system needs enough visual polish to impress.
- It also needs enough density to show metrics, contracts, audit events, and
  privacy guarantees without extra explanation.
- Motion should support comprehension, not perform for attention.

## Design-System References

Use the local `awesome-design-systems` catalogue as a reference map. The current
pilot console should borrow from:

- Carbon/Cloudscape/Elastic: dense operational hierarchy, metric blocks, and
  clear data tables.
- Blueprint/Astro UXDS: mission-console composition, dark technical surfaces,
  and controlled status language.
- Atlassian/GitLab/Primer: restrained interaction states and direct UI copy.

Do not copy a system wholesale. TrustFaceChain needs its own recognizable
language: dark identity stage, connected trust pipeline, cryptographic assurance
rail, and concise operator controls.

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

Use an application-console layout:

- left navigation rail,
- top status bar,
- trust pipeline strip,
- main work surface,
- biometric sample stage,
- right-side assurance/model rail.

Recommended routes:

- `/enroll`
- `/verify`
- `/audit`
- `/models`
- `/evaluation`
- `/settings`

## Component Language

### Identity Console

Use a focused work panel:

- image/text input,
- biometric sample stage,
- consent summary,
- selected model,
- enroll/verify/revoke actions,
- latest assurance state.

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
