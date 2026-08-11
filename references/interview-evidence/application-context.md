# Application Context Resolver

Use this module before `prep`, `practice`, `mock`, or application-specific `analyze`.

## Goal

Resolve exactly what the interviewer is likely to see. Never silently substitute a newer resume for a submitted one.

## Resolution order

1. Match an explicit application ID.
2. Otherwise match company + role against `applications/*/context.json`.
3. If multiple active matches remain, ask the candidate to choose.
4. Verify every referenced path stays inside the workspace, exists, and matches its recorded SHA-256 before treating it as available.
5. Select context mode:
   - `submitted_application`: JD + submitted resume resolve.
   - `tailored_application`: JD + tailored resume resolve, submitted version absent.
   - `jd_plus_resume`: JD + master/current resume only.
   - `resume_only`: resume only.
   - `conversation_only`: no durable artifacts.

## Artifact precedence

`submitted_resume` > `tailored_resume` > `master_resume` > conversational resume content.

The lower-precedence artifact may supplement background but must not replace the artifact the interviewer received.

## Context packet

Return a compact internal packet:

- application ID, company, role, round ID, format;
- context mode and coverage limitations;
- JD must-haves and repeated competencies;
- resume artifact used and its immutable path;
- active Claim IDs that occur in that artifact;
- linked Project Deep Dives and Storybank entries;
- open/resurfaced Weak Points;
- prior factual feedback for this application.

Do not load unrelated applications, retired Claims, resolved Weak Points, or the entire question bank.

## Degraded-mode disclosure

When context mode is not `submitted_application`, say so once before application-specific coaching:

> I can tailor this to [available artifacts], but I cannot verify the exact resume the interviewer received. I’ll mark that coverage limitation rather than imply full application coverage.

Continue unless the missing artifact materially prevents the requested task.

## Write rules

- `context.json` owns company, role, status, artifact paths, and round facts.
- Never overwrite a submitted artifact. Store its SHA-256 and `locked_at`; a mismatch invalidates `submitted_application` mode and requires a new version/path or explicit restoration.
- Add a new path/version when the candidate submitted a revision.
- `coaching_state.md` may summarize the active loop but is not authoritative for artifact paths.

Use `scripts/register_application_artifact.py` to create a content-addressed snapshot and update the context record. Do not register a mutable external path as a submitted artifact.
