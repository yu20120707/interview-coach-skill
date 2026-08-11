#!/usr/bin/env python3
"""Snapshot and hash an application artifact without overwriting prior bytes."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, tempfile
from pathlib import Path

KINDS = {"jd", "submitted_resume", "tailored_resume", "master_resume"}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def atomic_json(path: Path, data: dict) -> None:
    fd,tmp=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except BaseException: Path(tmp).unlink(missing_ok=True); raise

def snapshot(workspace: Path, application_id: str, kind: str, source: Path) -> Path:
    workspace=workspace.resolve(); source=source.resolve()
    if kind not in KINDS: raise ValueError(f"unsupported artifact kind: {kind}")
    if re.fullmatch(r"app_[a-z0-9_]+", application_id) is None: raise ValueError("application_id must match app_[a-z0-9_]+")
    if not source.is_file(): raise ValueError(f"source is not a file: {source}")
    context_path=(workspace/"applications"/application_id/"context.json").resolve()
    try: context_path.relative_to(workspace)
    except ValueError: raise ValueError("application context escapes the workspace")
    if not context_path.is_file(): raise ValueError(f"application context not found: {context_path}")
    context=json.loads(context_path.read_text(encoding="utf-8")); digest=sha256(source); suffix=source.suffix or ".txt"
    name=f"{kind.replace('_','-')}-{digest[:12]}{suffix}"; destination=context_path.parent/name
    if not destination.exists():
        fd,tmp=tempfile.mkstemp(prefix=f".{name}.",suffix=".tmp",dir=destination.parent); os.close(fd)
        try: shutil.copyfile(source,tmp); os.replace(tmp,destination)
        except BaseException: Path(tmp).unlink(missing_ok=True); raise
    elif sha256(destination)!=digest: raise RuntimeError(f"existing snapshot hash mismatch: {destination}")
    ref={"path":str(destination.relative_to(workspace)),"sha256":digest}
    if kind=="submitted_resume": ref["locked_at"]=dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
    context["artifacts"][kind]=ref; atomic_json(context_path,context); return destination

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("workspace",type=Path); p.add_argument("application_id"); p.add_argument("kind",choices=sorted(KINDS)); p.add_argument("source",type=Path); a=p.parse_args()
    try: print(snapshot(a.workspace,a.application_id,a.kind,a.source))
    except (ValueError,RuntimeError,json.JSONDecodeError) as exc: p.error(str(exc))
    return 0

if __name__=="__main__": raise SystemExit(main())
