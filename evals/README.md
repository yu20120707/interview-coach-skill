# Evidence-aware regression suite

Run `python3 scripts/validate_evidence.py`.

The suite verifies all v1.0 contracts, invalid types/enums/additional fields, high-risk probe requirements, question-plan totals, parent links, Weak Point resolution proof, workspace path containment, hashes, and cross-record references.

Workspace initialization can be smoke-tested with a temporary directory, followed by `validate_evidence.py --kind claim <path>` and `--kind weak_points <path>`.

Behavioral acceptance scenarios are documented in `docs/implementation-plan.md` and should be exercised manually in a compatible agent environment because the Skill itself is prompt-driven.
