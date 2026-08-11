# Phase 0–4 implementation record

## Phase 0 — Baseline and boundaries

- ADR fixes the product boundary: Interview Coach remains the only command surface.
- Existing five-dimension scoring and one-question-at-a-time behavior remain authoritative.

## Phase 1 — Evidence model

- v1.0 schemas for Claims, application context, Project Deep Dive, interview session, and Weak Points.
- Empty workspace templates and Workspace Adapter ownership rules.
- Backward-compatible coaching-state migration.

## Phase 2 — Application-aware grilling

- Submitted-artifact precedence and degraded modes.
- Claim risk/defensibility, Question Planner, and Progressive Probing.
- Integration into `prep`, `practice`, and `mock`.

## Phase 3 — Feedback loop

- Observed/inferred separation and Weak Point lifecycle.
- Integration into `analyze`, `debrief`, `feedback`, `stories`, and state triggers.

## Phase 4 — Calibration and validation

- Evidence priority, Claim calibration, coverage metrics, fixtures, migration, and documentation.

## Manual acceptance scenarios

1. A submitted metric Claim without attribution becomes high-risk and receives measurement, trade-off, and failure probes.
2. Definition knowledge without TTL/consistency reasoning cannot score high on Substance/Credibility.
3. An ownership contradiction produces observed evidence and a defensibility recommendation.
4. Good mocks plus repeated poor real outcomes trigger drift investigation, not an automatic global downgrade.
5. External wording and coach inference remain separate records.
6. A resolved gap that fails later becomes resurfaced.
7. Missing submitted resume produces a visible degraded-mode limitation.
