#!/usr/bin/env python3
"""Initialize optional evidence-aware state without overwriting candidate data."""
from __future__ import annotations
import argparse, json, os, re, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "workspace-template"

def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True); raise

def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not slug: raise ValueError("company/role must contain an ASCII letter or digit")
    return slug

def initialize(workspace: Path, company: str | None, role: str | None) -> list[Path]:
    workspace = workspace.resolve(); workspace.mkdir(parents=True, exist_ok=True); created = []
    for name in ("claims.json", "weak-points.json"):
        destination = workspace / name
        if not destination.exists():
            atomic_json(destination, json.loads((TEMPLATE / name).read_text(encoding="utf-8"))); created.append(destination)
    if company or role:
        if not (company and role): raise ValueError("--company and --role must be provided together")
        app_id = f"app_{safe_slug(company)}_{safe_slug(role)}"; app_dir = workspace / "applications" / app_id; context = app_dir / "context.json"
        if not context.exists():
            app_dir.mkdir(parents=True, exist_ok=True); (app_dir / "interview").mkdir(exist_ok=True)
            atomic_json(context, {"schema_version":"1.0","id":app_id,"company":company,"role":role,"status":"preparing","artifacts":{},"rounds":[]}); created.append(context)
    return created

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("workspace",type=Path); parser.add_argument("--company"); parser.add_argument("--role"); args=parser.parse_args()
    try: created=initialize(args.workspace,args.company,args.role)
    except ValueError as exc: parser.error(str(exc))
    for path in created: print(path)
    if not created: print("Evidence workspace already initialized; no files changed.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
