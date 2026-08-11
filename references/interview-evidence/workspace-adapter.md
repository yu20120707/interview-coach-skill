# Career Workspace Adapter

This adapter defines deterministic read/write behavior for evidence-aware coaching files.

## Default paths

```text
claims.json
weak-points.json
projects/<project-id>.json
applications/<application-id>/context.json
applications/<application-id>/jd.md
applications/<application-id>/submitted-resume.*
applications/<application-id>/interview/<session-id>.json
```

## Read protocol

1. Resolve paths relative to the active coaching workspace.
2. Reject traversal outside the workspace.
3. Parse JSON and require a supported `schema_version`.
4. Validate stable IDs, path containment, file existence, and recorded hashes before use.
5. Load only records relevant to the active command/application.
6. Report invalid records as coverage limitations; do not guess missing values.

## Write protocol

1. Read the current version immediately before mutation.
2. Apply the smallest update.
3. Validate the complete document against its schema.
4. Write to a sibling temporary file.
5. Atomically replace the destination.
6. Update `coaching_state.md` summaries only after the structured write succeeds.

## Supported version

Current evidence schema version: `1.0`.

Unknown major versions are read-only blockers. Additive compatible fields require a documented schema update before use.

## Ownership boundary

Structured files own artifact facts, Claims, sessions, and Weak Points. `coaching_state.md` owns coaching preferences, strategy, score trend summary, and human-readable loop overview.
