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


def validate_file(path: Path) -> list[str]:
    errors = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        Project.model_validate(data)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
    return errors


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
    for f in files:
        errs = validate_file(f)
        if errs:
            all_errors.extend(errs)
            for e in errs:
                print(f"FAIL  {e}")
        else:
            print(f"  OK  {f.name}")

    print()
    if all_errors:
        print(f"{len(all_errors)} error(s) found.")
        sys.exit(1)
    else:
        print(f"All {len(files)} file(s) valid.")


if __name__ == "__main__":
    main()
