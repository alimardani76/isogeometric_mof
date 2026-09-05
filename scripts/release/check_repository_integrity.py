#!/usr/bin/env python3
"""Repository-integrity checks for the Paper 7B public-release branch.

This script performs release-engineering checks only. It does not execute the
scientific workflow or validate scientific results.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_TRACKED_BYTES = 25 * 1024 * 1024

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".zip",
    ".tar.gz",
)

FORBIDDEN_PATH_PARTS = (
    "__pycache__",
    "/raw/",
    "validation/raspa/raw/",
    "validation/raspa/runs/",
    "validation/raspa/closure/",
    "structural_panel/OVITO_screening/",
    "structural_panel/OVITO_final_HR/contact_sheets/",
    "structural_panel/OVITO_final_insets_tight/",
    "/contact_sheets/",
    "/xyz_fragments/",
)

PUBLIC_TEXT_PREFIXES = (
    "README.md",
    "archive/",
    "environment/",
    "figures/",
    "provenance/",
    "validation/",
    "structural_panel/",
)

LOCAL_PATH_MARKERS = (
    "C:\\Users\\",
    "/home/",
    "\\Desktop\\",
    "/mnt/c/Users/",
)


def tracked_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8", errors="strict")
    return [ROOT / item for item in out.split("\0") if item]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_forbidden_paths(files: list[Path], errors: list[str]) -> None:
    for path in files:
        r = rel(path)
        lower = r.lower()

        if lower.endswith(FORBIDDEN_SUFFIXES):
            errors.append(f"forbidden tracked artifact: {r}")

        normalized = f"/{r}/"
        for part in FORBIDDEN_PATH_PARTS:
            if part in normalized or r.startswith(part):
                errors.append(f"forbidden tracked path: {r}")
                break


def check_file_sizes(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_TRACKED_BYTES:
            errors.append(
                f"tracked file exceeds {MAX_TRACKED_BYTES // (1024 * 1024)} MiB: "
                f"{rel(path)} ({size} bytes)"
            )


def check_python(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
            ast.parse(source, filename=rel(path))
        except Exception as exc:
            errors.append(f"invalid Python syntax: {rel(path)}: {exc}")


def check_json(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix != ".json":
            continue
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                json.load(handle)
        except Exception as exc:
            errors.append(f"invalid JSON: {rel(path)}: {exc}")


def check_csv(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix != ".csv" or not path.is_file():
            continue
        if path.stat().st_size == 0:
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for _ in csv.reader(handle):
                    pass
        except Exception as exc:
            errors.append(f"unreadable CSV: {rel(path)}: {exc}")


def check_public_text_for_local_paths(files: list[Path], errors: list[str]) -> None:
    text_suffixes = {".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".py", ".bat"}
    for path in files:
        r = rel(path)
        if not any(r == prefix or r.startswith(prefix) for prefix in PUBLIC_TEXT_PREFIXES):
            continue
        if path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for marker in LOCAL_PATH_MARKERS:
            if marker in text:
                errors.append(f"local path marker {marker!r} in public-facing file: {r}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_structural_panel_manifest(files: list[Path], errors: list[str]) -> None:
    module = ROOT / "structural_panel"
    manifest = module / "data" / "manifests" / "REPO_PAYLOAD_SHA256.csv"

    if not module.exists():
        errors.append("structural_panel module is missing")
        return
    if not manifest.is_file():
        errors.append("structural_panel payload manifest is missing")
        return

    expected: dict[str, tuple[int, str]] = {}
    try:
        with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                p = row["path"].strip().replace("\\", "/")
                expected[p] = (int(row["bytes"]), row["sha256"].strip().lower())
    except Exception as exc:
        errors.append(f"cannot parse structural-panel manifest: {exc}")
        return

    # Keep the original private-handoff manifest unchanged as provenance.
    if len(expected) != 100:
        errors.append(
            f"structural-panel original manifest expected 100 payload rows, found {len(expected)}"
        )

    external_cifs = {
        p for p in expected
        if p.startswith("data/cifs/") and p.lower().endswith(".cif")
    }
    adapted_docs = {"README.md"}
    frozen_public = {
        p: v for p, v in expected.items()
        if p not in external_cifs and p not in adapted_docs
    }

    if len(external_cifs) != 12:
        errors.append(
            f"structural-panel expected 12 external CIF provenance rows, found {len(external_cifs)}"
        )
    if len(frozen_public) != 87:
        errors.append(
            f"structural-panel expected 87 frozen public payload rows, found {len(frozen_public)}"
        )

    # Verify all immutable public payload bytes against the original manifest.
    for p, (expected_size, expected_hash) in frozen_public.items():
        target = module / p
        if not target.is_file():
            errors.append(f"structural-panel frozen public file missing: {p}")
            continue
        actual_size = target.stat().st_size
        if actual_size != expected_size:
            errors.append(
                f"structural-panel size mismatch: {p}: {actual_size} != {expected_size}"
            )
            continue
        actual_hash = sha256_file(target)
        if actual_hash != expected_hash:
            errors.append(
                f"structural-panel SHA-256 mismatch: {p}: {actual_hash} != {expected_hash}"
            )

    # README is intentionally adapted for the public external-CIF boundary.
    if not (module / "README.md").is_file():
        errors.append("structural-panel release-adapted README.md is missing")

    # Third-party CIF byte files must not be present in the public release.
    for p in sorted(external_cifs):
        if (module / p).exists():
            errors.append(
                f"third-party structural CIF must be external in public release: {p}"
            )

    tracked = {
        rel(path).removeprefix("structural_panel/")
        for path in files
        if rel(path).startswith("structural_panel/")
    }

    allowed = set(frozen_public)
    allowed.add("README.md")
    allowed.add("data/manifests/REPO_PAYLOAD_SHA256.csv")

    missing_tracked = allowed - tracked
    unexpected_tracked = tracked - allowed
    for p in sorted(missing_tracked):
        errors.append(f"structural-panel expected tracked file missing: {p}")
    for p in sorted(unexpected_tracked):
        errors.append(f"structural-panel unexpected tracked file: {p}")

    if len(tracked) != 89:
        errors.append(
            f"structural-panel expected 89 tracked public files, found {len(tracked)}"
        )

def main() -> int:
    files = tracked_files()
    errors: list[str] = []

    check_forbidden_paths(files, errors)
    check_file_sizes(files, errors)
    check_python(files, errors)
    check_json(files, errors)
    check_csv(files, errors)
    check_public_text_for_local_paths(files, errors)
    check_structural_panel_manifest(files, errors)

    if errors:
        print("Repository integrity check FAILED:")
        for item in errors:
            print(f" - {item}")
        return 1

    print(f"Repository integrity check PASSED for {len(files)} tracked files.")
    print("Structural panel: 89 tracked public files; 87 frozen payload hashes PASS; 12 CIF provenance entries external; release README adapted.")
    print("Checked: paths/artifacts, file sizes, Python syntax, JSON, CSV, local paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
