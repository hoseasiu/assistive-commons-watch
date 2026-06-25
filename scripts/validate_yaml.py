#!/usr/bin/env python3
"""
Validate all YAML files in _data/projects/ against the Project Pydantic model.

Usage:
    python scripts/validate_yaml.py [path/to/project.yaml ...]

With no arguments validates every *.yaml file under _data/projects/.
Exits non-zero if any file fails.
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from _fetchers.models import Project


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        project = Project.model_validate(data)
        if not project.iso_9999_codes:
            warnings.append(f"{path.name}: iso_9999_codes is missing or empty")
        if "at_relevance" not in data:
            warnings.append(f"{path.name}: at_relevance not explicitly set (defaulting to primary)")
    except Exception as exc:
        errors.append(f"{path}: {exc}")
    return errors, warnings


def main() -> None:
    if len(sys.argv) > 1:
        files = [Path(p) for p in sys.argv[1:]]
    else:
        root = Path(__file__).parent.parent / "_data" / "projects"
        files = sorted(f for f in root.glob("*.yaml") if f.name != ".gitkeep")

    if not files:
        print("No YAML files found.")
        sys.exit(0)

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for f in files:
        errs, warns = validate_file(f)
        if errs:
            all_errors.extend(errs)
            for e in errs:
                print(f"FAIL  {e}")
        elif warns:
            for w in warns:
                print(f"WARN  {w}")
            all_warnings.extend(warns)
        else:
            print(f"  OK  {f.name}")

    print()
    if all_errors:
        print(f"{len(all_errors)} error(s) found.")
        sys.exit(1)
    else:
        summary = f"All {len(files)} file(s) valid."
        if all_warnings:
            summary += f"  ({len(all_warnings)} warning(s))"
        print(summary)


if __name__ == "__main__":
    main()
