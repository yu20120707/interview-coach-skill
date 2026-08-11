# ADR-001: Evidence-aware interview coaching

- Status: Accepted
- Date: 2026-08-10

## Context

Interview Coach provides the primary coaching experience, five-dimension scorecard, Storybank, adaptive drills, mocks, transcript analysis, and outcome calibration. `ai-career-toolkit` demonstrates useful interview-stage mechanisms: binding questions to submitted artifacts, tracking risky claims, project deep dives, and persistent weak points.

Importing the complete toolkit would duplicate resume/application workflows and create a second interview engine.

## Decision

Keep Interview Coach as the product and command surface. Selectively implement application context resolution, Claim risk/defensibility, Project Deep Dives, evidence-aware question planning, progressive probes, and Weak Point lifecycle inside existing commands.

Use the existing five dimensions as the only human-facing scorecard. A–D probe grades are internal evidence. Keep structured facts in small versioned JSON files and coaching preferences/strategy in `coaching_state.md`.

## State ownership

- `context.json`: company, role, artifact paths, rounds.
- `claims.json`: attackable statements, evidence, risk, defensibility.
- Project Deep Dive JSON: project facts, decisions, unknowns, Claim/Story links.
- Session JSON: plan, question units, probe evidence, core scores.
- `weak-points.json`: material gap evidence and lifecycle.
- `coaching_state.md`: preferences, summaries, score trends, active coaching strategy.

## Consequences

Positive: exact submitted-version coaching, consistent high-risk probing, separable facts/inference, and backward-compatible Markdown-only use.

Trade-offs: more local files, stricter artifact hygiene, and a requirement to evolve schemas and command references together.

## Rejected alternatives

- Merge all of `ai-career-toolkit`: too broad and duplicates the product surface.
- Keep `interview-griller` as a separate command: competing engines and scores.
- Put everything in `coaching_state.md`: weak auditability and immutable-artifact handling.
- Require structured state for all users: breaks the quick-start experience.

## Attribution

Design inspiration for application-aware grilling, Claim risk, Project Deep Dive, and feedback separation came from the MIT-licensed `yu20120707/ai-career-toolkit`. No complete module is vendored; adapted concepts are implemented in Interview Coach's architecture.
