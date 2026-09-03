#!/usr/bin/env python3
from __future__ import annotations
import base64, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / ".bootstrap"

parts = sorted(BOOT.glob("payload.part*"))
if not parts:
    raise SystemExit("No payload parts found")

encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
files = payload.get("files", [])
if len(files) != 75:
    raise SystemExit(f"Expected 75 payload files, got {len(files)}")

for item in files:
    rel = Path(item["path"])
    if rel.is_absolute() or ".." in rel.parts or rel.parts[0] != "structural_panel":
        raise SystemExit(f"Unsafe payload path: {rel}")
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if item.get("encoding") != "base64":
        raise SystemExit(f"Unsupported encoding for {rel}")
    target.write_bytes(base64.b64decode(item["content"]))

# Verify no transport-generated Python cache is present.
for p in ROOT.joinpath("structural_panel").rglob("__pycache__"):
    shutil.rmtree(p)

subprocess.run(["python3", "-m", "compileall", "-q", "structural_panel"], cwd=ROOT, check=True)
for p in ROOT.joinpath("structural_panel").rglob("__pycache__"):
    shutil.rmtree(p)

subprocess.run(["python3", "scripts/release/check_repository_integrity.py"], cwd=ROOT, check=True)

# Remove one-time transport files and workflow from the resulting source tree.
shutil.rmtree(BOOT)
wf = ROOT / ".github" / "workflows" / "structural-bootstrap.yml"
if wf.exists():
    wf.unlink()

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=True)
subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
subprocess.run(["git", "diff", "--cached", "--check"], cwd=ROOT, check=True)

status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
print(status)
subprocess.run(["git", "commit", "-m", "feat(structural-panel): add curated reproducible source tree"], cwd=ROOT, check=True)
subprocess.run(["git", "push", "origin", "HEAD:release/paper7b-public"], cwd=ROOT, check=True)
