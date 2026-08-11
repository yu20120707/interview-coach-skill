# Claim Risk and Defensibility Engine

Claims are concrete statements an interviewer may attack. Store them in `claims.json` using `references/schemas/claim.schema.json`.

## Claim extraction

Extract a Claim only when a statement contains at least one of:

- measurable impact, scale, latency, revenue, cost, quality, or adoption;
- ownership or leadership scope;
- architecture, technology, migration, reliability, or security depth;
- a strong causal assertion;
- a differentiating claim central to role fit.

Do not turn routine factual lines into Claims merely to increase coverage.

## Evidence hierarchy

1. User-confirmed detail with a coherent explanation.
2. Source document or transcript.
3. Measurement record or credible estimation basis.
4. Adjacent evidence.
5. Coach inference.

Inference may identify a question; it cannot activate or strengthen a Claim.

## Risk classification

Set `high` when any applies:

- exact or material metric lacks a measurement basis;
- ownership language exceeds recorded decision/execution scope;
- the architecture cannot be reached from known project facts;
- failure behavior, consistency, security, or trade-offs are central but unexplained;
- the Claim is essential to the target role and currently untested.

Set `medium` for plausible, partly evidenced statements with one meaningful gap. Set `low` only when evidence, ownership, and explanation are coherent.

## Required probes

Every high-risk Claim must have at least three distinct probe types. Use the most relevant of:

`fact`, `mechanism`, `ownership`, `measurement`, `tradeoff`, `failure`, `alternative`, `counterfactual`.

Metrics require `measurement`; architecture Claims require `tradeoff` or `alternative`; broad ownership requires `ownership`; production/reliability Claims require `failure`.

## Defensibility transitions

- `untested` → `weak`: a material C/D answer or contradiction.
- `untested` → `adequate`: passes at least three required probes with no material contradiction.
- `adequate` → `strong`: passes a later adversarial chain including trade-off or counterfactual.
- `strong|adequate` → `weak`: real feedback or repeated failure contradicts the prior assessment.
- any → `retired`: candidate explicitly removes it or evidence shows it should not be used.

Do not upgrade based on polished delivery alone. Do not downgrade silently: cite the session/question evidence and recommend the change.

## Output in coaching

Present a concise Claim Risk Map:

| Claim | Source | Risk | Defensibility | Missing proof | Next probe |

Keep internal IDs available but avoid cluttering normal coaching language unless they help disambiguate.
