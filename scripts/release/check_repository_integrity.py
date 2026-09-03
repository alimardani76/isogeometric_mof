#!/usr/bin/env python3
"""Repository-integrity checks for the Paper 7B public-release branch.

This script performs release-engineering checks only. It does not execute the
scientific workflow or validate scientific results.
"""

from __future__ import annotations

import ast
import csv
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
            # Historical audits may intentionally preserve an empty placeholder.
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.reader(handle)
                for _ in reader:
                    pass
        except Exception as exc:
            errors.append(f"unreadable CSV: {rel(path)}: {exc}")


def check_public_text_for_local_paths(files: list[Path], errors: list[str]) -> None:
    for path in files:
        r = rel(path)
        if not any(r == prefix or r.startswith(prefix) for prefix in PUBLIC_TEXT_PREFIXES):
            continue
        if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for marker in LOCAL_PATH_MARKERS:
            if marker in text:
                errors.append(f"local path marker {marker!r} in public-facing file: {r}")


def main() -> int:
    files = tracked_files()
    errors: list[str] = []

    check_forbidden_paths(files, errors)
    check_file_sizes(files, errors)
    check_python(files, errors)
    check_json(files, errors)
    check_csv(files, errors)
    check_public_text_for_local_paths(files, errors)

    if errors:
        print("Repository integrity check FAILED:")
        for item in errors:
            print(f" - {item}")
        return 1

    print(f"Repository integrity check PASSED for {len(files)} tracked files.")
    print("Checked: paths/artifacts, file sizes, Python syntax, JSON, CSV, local paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
