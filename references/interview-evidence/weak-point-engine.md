# Weak Point Feedback Engine

Weak Points turn demonstrated gaps into reusable training priorities. Store them in `weak-points.json`.

## Creation threshold

Create or update a Weak Point when any applies:

- a C/D answer exposes a material gap;
- the same gap appears in two answers or sessions;
- factual recruiter/interviewer feedback identifies it;
- a high-risk Claim cannot survive a required probe;
- a gap materially changes the hiring signal.

Do not persist stylistic micro-feedback or one-off hesitation with no hiring relevance.

## Evidence classification

- `observed`: candidate answer/transcript or verbatim/faithful external feedback.
- `inferred`: coach diagnosis or hypothesized root cause.

Never rewrite inference as observation. Preserve external wording where possible.

## Deduplication

Match in order:

1. same Claim ID + same failure mode;
2. same normalized topic + linked dimension;
3. same root cause with materially equivalent next drill.

If matched, append evidence and update severity/status instead of creating a new ID.

## Lifecycle

- new material issue → `open`;
- improvement across one later test → `improving`;
- two successful later tests, including one adversarial/relevant test → `resolved`; record both in `resolution_evidence` with session/unit, probe type, adversarial flag, and timestamp;
- failure after resolution → `resurfaced`, increment recurrence, raise priority;

High-severity items cannot resolve from self-report alone.

## Severity

- `high`: invalidates an important Claim, repeats, or creates a likely no-hire signal.
- `medium`: meaningful but bounded gap with a clear drill.
- `low`: useful refinement that does not currently change the hiring signal.

## Required output

Every open/improving/resurfaced item needs one concrete `next_drill`. `progress` shows at most the top three by severity, recurrence, and target-role relevance.
