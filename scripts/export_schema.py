#!/usr/bin/env python3
"""
Export Project JSON Schema to schema.json.

This file is a CI build artifact — do not edit schema.json by hand.
Run: python scripts/export_schema.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from _fetchers.models import Project


def main() -> None:
    schema = Project.model_json_schema()
    out = Path(__file__).parent.parent / "schema.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"schema.json written ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
