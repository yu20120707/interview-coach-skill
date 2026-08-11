# Evidence-Aware Question Planner

Build this internal plan before asking the first question in application-aware `practice` or `mock`. Do not show the full plan unless the candidate asks.

## Default allocation

| Source | Weight | Rule |
|---|---:|---|
| High-value/high-risk Claims | 35% | Each selected high-risk Claim gets a 3–7 layer chain. |
| JD must-haves | 25% | Prefer the JD's wording and observable bar. |
| Open/resurfaced Weak Points | 20% | Prioritize high severity and recurrence. |
| Current round/format | 10% | Reflect recruiter, HM, technical, panel, case, or system-design needs. |
| New/general ability | 10% | Use after material coverage is protected. |

Weights are targets, not quotas. Record actual covered sources in the session.

## Rebalancing

- No active Claims: move Claim weight to JD and Weak Points.
- No prior Weak Points: split their weight between Claims and JD.
- Recruiter screen: emphasize relevance, positioning, transitions, and credibility.
- Technical deep dive: increase Claim and Project Deep Dive coverage.
- Hiring manager: increase ownership, judgment, outcomes, and role-fit concerns.
- Panel: distribute competencies and avoid repeating the same story.
- Context degraded: reduce certainty; never invent source coverage.

## Selection constraints

- Test the exact submitted wording before a paraphrased stronger version.
- Prefer active Claims from the selected application.
- Do not reuse one story for more than two major questions unless testing adaptability explicitly.
- Include at least one question that tests an existing strength; this prevents a plan made only of weaknesses.
- Include at least one recovery opportunity after a C/D answer.

## Plan record

Write allocation fractions and covered source identifiers into `interview-session.json`. Fractions should sum to approximately 1.0 (±0.01).
