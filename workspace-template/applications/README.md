# Application interview contexts

Create one directory per application:

```text
applications/app_<company>_<role>/
  context.json
  jd.md
  submitted-resume.md     # immutable after submission
  interview/
```

The initializer leaves `artifacts` empty so a placeholder cannot be mistaken for a real JD. Add the exact JD snapshot, compute its SHA-256, and then register `{ "path": ..., "sha256": ... }` in `context.json`.

Validate `context.json` with `references/schemas/application-context.schema.json`. A submitted resume reference also requires `sha256` and `locked_at`. Never overwrite a submitted resume with a later edit; use a new version/path.
