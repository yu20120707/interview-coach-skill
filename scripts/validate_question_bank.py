#!/usr/bin/env python3
"""Validate the bundled technical question-bank manifest and source files."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BANK=ROOT/"references"/"question-bank"

def main() -> int:
    errors=[]
    try: manifest=json.loads((BANK/"manifest.json").read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: print(f"FAIL manifest: {exc}",file=sys.stderr); return 1
    required={"schema_version","purpose","source_repository","source_commit","source_path","license","entries"}
    missing=required-set(manifest)
    if missing: errors.append(f"manifest missing: {', '.join(sorted(missing))}")
    if manifest.get("schema_version")!="1.0": errors.append("unsupported schema_version")
    if manifest.get("source_repository") != "https://github.com/yu20120707/ai-career-toolkit":
        errors.append("unexpected source_repository")
    if manifest.get("source_path") != "interview-griller/references/question-bank":
        errors.append("unexpected source_path")
    if not isinstance(manifest.get("purpose"), str) or not manifest["purpose"].strip():
        errors.append("purpose must be a non-empty string")
    if manifest.get("license")!="MIT": errors.append("question bank must preserve MIT license metadata")
    if re.fullmatch(r"[a-f0-9]{40}",str(manifest.get("source_commit",""))) is None: errors.append("invalid source_commit")
    entries=manifest.get("entries")
    if not isinstance(entries,list): errors.append("entries must be an array"); entries=[]
    seen_ids=set(); seen_paths=set(); declared=set()
    for index,entry in enumerate(entries):
        label=f"entries[{index}]"
        if not isinstance(entry,dict): errors.append(f"{label} must be an object"); continue
        for key in ("id","path","sha256","kind","priority","topics","use_for","boundary"):
            if key not in entry: errors.append(f"{label} missing {key}")
        entry_id=entry.get("id"); relative=entry.get("path")
        if not isinstance(entry_id,str) or re.fullmatch(r"[a-z0-9-]+",entry_id) is None: errors.append(f"{label} invalid id")
        elif entry_id in seen_ids: errors.append(f"duplicate id: {entry_id}")
        else: seen_ids.add(entry_id)
        if not isinstance(relative,str): errors.append(f"{label} invalid path"); continue
        if relative in seen_paths: errors.append(f"duplicate path: {relative}")
        seen_paths.add(relative); declared.add(relative)
        target=(BANK/relative).resolve()
        try: target.relative_to(BANK.resolve())
        except ValueError: errors.append(f"path escapes question bank: {relative}"); continue
        if not target.is_file(): errors.append(f"missing source: {relative}"); continue
        if target.suffix.lower()!=".md": errors.append(f"source is not Markdown: {relative}")
        try: content=target.read_text(encoding="utf-8")
        except UnicodeDecodeError: errors.append(f"source is not UTF-8: {relative}"); continue
        if len(content.strip())<100: errors.append(f"source is unexpectedly empty: {relative}")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if entry.get("sha256") != digest: errors.append(f"source hash mismatch: {relative}")
        if entry.get("kind") not in {"real_interview","fundamentals"}: errors.append(f"{label} invalid kind")
        if entry.get("priority") not in {"high","medium","low"}: errors.append(f"{label} invalid priority")
        if not _non_empty_strings(entry.get("topics")): errors.append(f"{label} requires non-empty string topics")
        if not _non_empty_strings(entry.get("use_for")): errors.append(f"{label} requires non-empty string use_for values")
        if not isinstance(entry.get("boundary"),str) or not entry.get("boundary").strip(): errors.append(f"{label} requires boundary")
    actual={str(p.relative_to(BANK)) for folder in ("fundamentals","real-interviews") for p in (BANK/folder).rglob("*.md")}
    for path in sorted(actual-declared): errors.append(f"undeclared source: {path}")
    for path in sorted(declared-actual): errors.append(f"declared source outside expected folders: {path}")
    expected_ids={"real-interviews-01","real-interviews-02","linux-full","mysql","operating-systems","networking","process-thread-coroutine","cpp-fundamentals","linux-concise"}
    if seen_ids!=expected_ids: errors.append(f"entry ID set mismatch: missing={sorted(expected_ids-seen_ids)}, extra={sorted(seen_ids-expected_ids)}")
    if errors:
        for error in errors: print(f"FAIL {error}",file=sys.stderr)
        return 1
    print(f"PASS question bank: {len(entries)} entries, {len(actual)} sources")
    return 0

def _non_empty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)

if __name__=="__main__": raise SystemExit(main())
