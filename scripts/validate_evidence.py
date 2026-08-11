#!/usr/bin/env python3
"""Validate evidence schemas, fixtures, and cross-record invariants."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "references" / "schemas"
CASES = ROOT / "evals" / "cases"

SCHEMA_FILES = {
    "claim": "claim.schema.json",
    "application": "application-context.schema.json",
    "session": "interview-session.schema.json",
    "weak_points": "weak-point.schema.json",
    "project": "project-deep-dive.schema.json",
}

VALID_CASES = {
    "claim": "claim-valid.json",
    "application": "application-context-valid.json",
    "session": "interview-session-valid.json",
    "weak_points": "weak-points-valid.json",
    "project": "project-deep-dive-valid.json",
}


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def schema_errors(schema: dict, data: object, path: str = "$") -> list[str]:
    """Validate the JSON-Schema subset used by the bundled v1.0 contracts."""
    errors: list[str] = []
    expected = schema.get("type")
    type_ok = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
        "boolean": lambda x: isinstance(x, bool),
    }
    if expected and not type_ok[expected](data):
        return [f"{path}: expected {expected}"]
    if "const" in schema and data != schema["const"]: errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and data not in schema["enum"]: errors.append(f"{path}: value {data!r} is not in enum")
    if isinstance(data, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in data: errors.append(f"{path}: missing required property {key}")
        if schema.get("additionalProperties") is False:
            for key in data.keys() - properties.keys(): errors.append(f"{path}: additional property {key} is not allowed")
        for key, value in data.items():
            child = properties.get(key)
            if child is not None: errors += schema_errors(child, value, f"{path}.{key}")
            elif isinstance(schema.get("additionalProperties"), dict): errors += schema_errors(schema["additionalProperties"], value, f"{path}.{key}")
    elif isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema:
            for index, value in enumerate(data): errors += schema_errors(item_schema, value, f"{path}[{index}]")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(x, sort_keys=True) for x in data]
            if len(normalized) != len(set(normalized)): errors.append(f"{path}: items must be unique")
    elif isinstance(data, str):
        if len(data) < schema.get("minLength", 0): errors.append(f"{path}: string is too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], data) is None: errors.append(f"{path}: does not match pattern")
        if schema.get("format") == "date":
            try: dt.date.fromisoformat(data)
            except ValueError: errors.append(f"{path}: invalid date")
        if schema.get("format") == "date-time":
            rfc3339 = re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", data)
            try: parsed = dt.datetime.fromisoformat(data.replace("Z", "+00:00")) if rfc3339 else None
            except ValueError: parsed = None
            if parsed is None or parsed.tzinfo is None: errors.append(f"{path}: invalid RFC 3339 date-time")
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]: errors.append(f"{path}: below minimum")
        if "maximum" in schema and data > schema["maximum"]: errors.append(f"{path}: above maximum")
    return errors


def validate(kind: str, data: object) -> list[str]:
    return schema_errors(load(SCHEMAS / SCHEMA_FILES[kind]), data)


def semantic_errors(kind: str, data: dict) -> list[str]:
    errors: list[str] = []
    if kind == "claim":
        for claim in data["claims"]:
            if claim["risk"] == "high" and len(set(claim["required_probes"])) < 3:
                errors.append(f"{claim['id']}: high-risk claims require at least three distinct probes")
    elif kind == "session":
        total = sum(data["question_plan"]["allocations"].values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"question plan allocations sum to {total:.3f}, expected 1.0±0.01")
        sequences = [unit["sequence"] for unit in data["units"]]
        if len(sequences) != len(set(sequences)):
            errors.append("session unit sequences must be unique")
        known = set(sequences)
        for unit in data["units"]:
            parent = unit.get("parent_sequence")
            if parent is not None and (parent not in known or parent >= unit["sequence"]):
                errors.append(f"unit {unit['sequence']}: parent_sequence must reference an earlier unit")
    elif kind == "weak_points":
        for item in data["weak_points"]:
            if item["status"] == "resolved":
                proof = item.get("resolution_evidence", [])
                if "resolved_at" not in item: errors.append(f"{item['id']}: resolved items require resolved_at")
                distinct={(x.get("session_id"),x.get("unit_sequence")) for x in proof}
                if len(distinct) < 2 or not any(x.get("adversarial") for x in proof): errors.append(f"{item['id']}: resolution requires two distinct successful later tests including one adversarial test")
            if item["severity"] == "high" and not any(e["kind"] == "observed" for e in item["evidence"]):
                errors.append(f"{item['id']}: high severity requires observed evidence")
    return errors


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): hasher.update(chunk)
    return hasher.hexdigest()


def contained_path(workspace: Path, relative: str) -> Path | None:
    candidate = (workspace / relative).resolve()
    try: candidate.relative_to(workspace)
    except ValueError: return None
    return candidate


def validate_workspace(workspace: Path) -> list[str]:
    workspace = workspace.resolve(); errors: list[str] = []
    records: dict[str, dict] = {}
    patterns = [("claim", workspace / "claims.json"), ("weak_points", workspace / "weak-points.json")]
    patterns += [("application", p) for p in workspace.glob("applications/*/context.json")]
    patterns += [("project", p) for p in workspace.glob("projects/*.json")]
    patterns += [("session", p) for p in workspace.glob("applications/*/interview/*.json")]
    for kind, path in patterns:
        if not path.exists(): continue
        try: data = load(path)
        except (OSError, json.JSONDecodeError) as exc: errors.append(f"{path}: {exc}"); continue
        current = validate(kind, data)
        if not current: current += semantic_errors(kind, data)
        errors += [f"{path.relative_to(workspace)}: {x}" for x in current]
        if not current: records[str(path)] = data
    def index(kind: str, values: list[tuple[str, dict]]) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for source, value in values:
            identifier = value["id"]
            if identifier in result: errors.append(f"{source}: duplicate {kind} ID {identifier}")
            else: result[identifier] = value
        return result

    claim_map = index("Claim", [(str(Path(path).relative_to(workspace)), item) for path,data in records.items() for item in data.get("claims", [])])
    weak_map = index("Weak Point", [(str(Path(path).relative_to(workspace)), item) for path,data in records.items() for item in data.get("weak_points", [])])
    project_map = index("Project", [(str(Path(path).relative_to(workspace)), data) for path,data in records.items() if data.get("id", "").startswith("project_")])
    application_map = index("Application", [(str(Path(path).relative_to(workspace)), data) for path,data in records.items() if data.get("id", "").startswith("app_")])
    session_map = index("Session", [(str(Path(path).relative_to(workspace)), data) for path,data in records.items() if data.get("id", "").startswith("session_")])
    claims=set(claim_map); weak_ids=set(weak_map)
    for key, data in records.items():
        path = Path(key)
        for claim_id in data.get("claim_ids", []):
            if claim_id not in claims: errors.append(f"{path.relative_to(workspace)}: unresolved Claim {claim_id}")
        if "artifacts" in data:
            for name, ref in data["artifacts"].items():
                if name == "claim_ids":
                    for claim_id in ref:
                        if claim_id not in claims: errors.append(f"{path.relative_to(workspace)}: unresolved Claim {claim_id}")
                    continue
                target = contained_path(workspace, ref["path"])
                if target is None: errors.append(f"{path.relative_to(workspace)}: artifact path escapes workspace: {ref['path']}"); continue
                if not target.is_file(): errors.append(f"{path.relative_to(workspace)}: artifact does not exist: {ref['path']}"); continue
                if ref.get("sha256") and digest(target) != ref["sha256"]: errors.append(f"{path.relative_to(workspace)}: artifact hash mismatch: {ref['path']}")
        for weak_id in data.get("weak_point_ids", []):
            if weak_id not in weak_ids: errors.append(f"{path.relative_to(workspace)}: unresolved Weak Point {weak_id}")
        for item in data.get("weak_points", []):
            for claim_id in item.get("claim_ids", []):
                if claim_id not in claims: errors.append(f"{path.relative_to(workspace)}: unresolved Claim {claim_id}")
        for unit in data.get("units", []):
            for claim_id in unit.get("claim_ids", []):
                if claim_id not in claims: errors.append(f"{path.relative_to(workspace)}: unresolved Claim {claim_id}")
        for claim in data.get("claims", []):
            source = claim.get("source", {})
            if claim.get("project_id") and claim["project_id"] not in project_map: errors.append(f"{path.relative_to(workspace)}: unresolved Project {claim['project_id']}")
            if source.get("application_id") and source["application_id"] not in application_map: errors.append(f"{path.relative_to(workspace)}: unresolved Application {source['application_id']}")
            if source.get("type") in {"submitted_resume", "tailored_resume", "master_resume", "application_answer"}:
                target = contained_path(workspace, source["path"])
                if target is None: errors.append(f"{path.relative_to(workspace)}: Claim source escapes workspace: {source['path']}")
                elif not target.is_file(): errors.append(f"{path.relative_to(workspace)}: Claim source does not exist: {source['path']}")
        if data.get("id", "").startswith("session_"):
            app_id=data.get("application_id"); round_id=data.get("round_id")
            if app_id and app_id not in application_map: errors.append(f"{path.relative_to(workspace)}: unresolved Application {app_id}")
            elif round_id and not any(x["id"]==round_id for x in application_map.get(app_id,{}).get("rounds",[])): errors.append(f"{path.relative_to(workspace)}: unresolved Round {round_id} for {app_id}")
        for item in data.get("weak_points", []):
            first=dt.datetime.fromisoformat(item["first_detected_at"].replace("Z","+00:00")) if item.get("first_detected_at") else None
            resolved=dt.datetime.fromisoformat(item["resolved_at"].replace("Z","+00:00")) if item.get("resolved_at") else None
            updated=dt.datetime.fromisoformat(item["updated_at"].replace("Z","+00:00"))
            tested_times=[]
            for proof in item.get("resolution_evidence", []):
                session=session_map.get(proof["session_id"])
                if session is None: errors.append(f"{path.relative_to(workspace)}: unresolved resolution Session {proof['session_id']}")
                else:
                    units={x["sequence"]:x for x in session["units"]}; unit=units.get(proof["unit_sequence"])
                    if unit is None: errors.append(f"{path.relative_to(workspace)}: unresolved unit {proof['unit_sequence']} in {proof['session_id']}")
                    elif unit["grade"] not in {"A","B"}: errors.append(f"{path.relative_to(workspace)}: resolution proof points to non-success grade {unit['grade']} in {proof['session_id']}#{proof['unit_sequence']}")
                    tested=dt.datetime.fromisoformat(proof["tested_at"].replace("Z","+00:00")); session_time=dt.datetime.fromisoformat(session["created_at"].replace("Z","+00:00")); tested_times.append(tested)
                    if tested < session_time: errors.append(f"{path.relative_to(workspace)}: resolution test predates its session")
                    if first and tested <= first: errors.append(f"{path.relative_to(workspace)}: resolution test must occur after first detection")
            if item.get("status")=="resolved" and resolved:
                if first and resolved < first: errors.append(f"{path.relative_to(workspace)}: resolved_at predates first detection")
                if tested_times and resolved < max(tested_times): errors.append(f"{path.relative_to(workspace)}: resolved_at predates resolution tests")
                if updated < resolved: errors.append(f"{path.relative_to(workspace)}: updated_at predates resolved_at")
    return errors


def run_fixture_suite() -> int:
    failures = 0
    for filename in SCHEMA_FILES.values():
        try:
            schema = load(SCHEMAS / filename)
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise ValueError("unexpected or missing $schema")
            print(f"PASS {filename} parses")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures += 1
            print(f"FAIL schema {filename}: {exc}")

    for kind, filename in VALID_CASES.items():
        data = load(CASES / filename)
        errors = validate(kind, data)
        if not errors: errors += semantic_errors(kind, data)
        if errors:
            failures += 1
            print(f"FAIL valid fixture {filename}: {'; '.join(errors)}")
        else:
            print(f"PASS {filename}")

    invalid = load(CASES / "claim-invalid-high-risk.json")
    errors = validate("claim", invalid)
    if not errors: errors += semantic_errors("claim", invalid)
    if not errors:
        failures += 1
        print("FAIL invalid fixture was accepted")
    else:
        print("PASS claim-invalid-high-risk.json rejected")

    adversarial = {
        "schema_version": "1.0", "id": "app_bad", "company": "X", "role": "Y",
        "status": "bogus", "artifacts": {"jd": {"path": "../../etc/passwd", "sha256": "x"}},
        "rounds": "oops", "extra": True
    }
    if not validate("application", adversarial):
        failures += 1; print("FAIL adversarial application was accepted")
    else: print("PASS adversarial application rejected")

    malformed_claims = {"schema_version": "1.0", "claims": "not-an-array"}
    if not validate("claim", malformed_claims):
        failures += 1; print("FAIL malformed Claim collection was accepted")
    else: print("PASS malformed Claim collection rejected without crashing")

    invalid_datetime = load(CASES / "interview-session-valid.json")
    invalid_datetime["created_at"] = "2026-08-10"
    if not validate("session", invalid_datetime):
        failures += 1; print("FAIL date-only value was accepted as date-time")
    else: print("PASS date-only value rejected as date-time")

    invalid_resolution = load(CASES / "weak-points-valid.json")
    invalid_resolution["weak_points"][0]["status"] = "resolved"
    invalid_resolution["weak_points"][0]["resolved_at"] = "2026-08-11T12:00:00Z"
    resolution_errors = validate("weak_points", invalid_resolution)
    if not resolution_errors: resolution_errors += semantic_errors("weak_points", invalid_resolution)
    if not resolution_errors:
        failures += 1; print("FAIL unsupported Weak Point resolution was accepted")
    else: print("PASS unsupported Weak Point resolution rejected")

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp); app_dir = workspace / "applications" / "app_bad"; app_dir.mkdir(parents=True)
        (workspace / "claims.json").write_text('{"schema_version":"1.0","claims":[]}', encoding="utf-8")
        (workspace / "weak-points.json").write_text('{"schema_version":"1.0","weak_points":[]}', encoding="utf-8")
        bad_context = {"schema_version":"1.0","id":"app_bad","company":"X","role":"Y","status":"preparing","artifacts":{"jd":{"path":"../../etc/passwd","sha256":"0"*64}},"rounds":[]}
        (app_dir / "context.json").write_text(json.dumps(bad_context), encoding="utf-8")
        if not validate_workspace(workspace):
            failures += 1; print("FAIL workspace path escape was accepted")
        else: print("PASS workspace path escape rejected")

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        duplicate_claims = {"schema_version":"1.0","claims":[
            {"id":"claim_dup","statement":"A","source":{"type":"user_statement","path":"conversation"},"project_id":"project_missing","evidence":[],"risk":"low","defensibility":"untested","status":"active","required_probes":[]},
            {"id":"claim_dup","statement":"B","source":{"type":"user_statement","path":"conversation","application_id":"app_missing"},"evidence":[],"risk":"low","defensibility":"untested","status":"active","required_probes":[]}
        ]}
        (workspace/"claims.json").write_text(json.dumps(duplicate_claims),encoding="utf-8")
        (workspace/"weak-points.json").write_text('{"schema_version":"1.0","weak_points":[]}',encoding="utf-8")
        cross_errors=validate_workspace(workspace)
        expected=("duplicate Claim ID","unresolved Project","unresolved Application")
        if not all(any(token in error for error in cross_errors) for token in expected):
            failures += 1; print("FAIL cross-record adversarial workspace was not fully rejected")
        else: print("PASS duplicate and orphan cross-record references rejected")

    required_refs = [
        ROOT / "references" / "interview-evidence" / name
        for name in [
            "application-context.md", "claim-risk-engine.md", "question-planner.md",
            "progressive-probing.md", "project-deep-dive.md", "weak-point-engine.md",
            "workspace-adapter.md",
        ]
    ]
    for path in required_refs:
        if not path.is_file():
            failures += 1
            print(f"FAIL missing reference {path.relative_to(ROOT)}")
        else:
            print(f"PASS {path.relative_to(ROOT)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=SCHEMA_FILES)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args()
    if args.workspace:
        errors = validate_workspace(args.workspace)
        if errors: print("\n".join(errors), file=sys.stderr); return 1
        print(f"PASS workspace {args.workspace}"); return 0
    if args.path:
        if not args.kind:
            parser.error("--kind is required when validating a path")
        data = load(args.path)
        errors = validate(args.kind, data)
        if not errors: errors += semantic_errors(args.kind, data)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"PASS {args.path}")
        return 0
    return 1 if run_fixture_suite() else 0


if __name__ == "__main__":
    raise SystemExit(main())
