#!/usr/bin/env python3
"""
Scaffold a new project YAML file in _data/projects/.

Usage:
    python scripts/add_project.py --url https://github.com/org/repo
    python scripts/add_project.py --url https://github.com/org/repo --no-prompt
    python scripts/add_project.py --url https://github.com/org/repo --slug my-slug

With --no-prompt all curated fields are left as null and no interactive prompts
are shown. This is useful for batch imports.

If GITHUB_TOKEN is set in the environment the script fetches the repo's name and
description from the GitHub API to pre-fill those fields.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yaml

# Make the repo root importable.
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from _fetchers.models import BuildDocsQuality, Modality, SkillLevel  # noqa: E402

PROJECTS_DIR = REPO_ROOT / "_data" / "projects"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_github_url(url: str) -> tuple[str, str, str]:
    """Return (owner, repo, default_slug) from a GitHub URL."""
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        sys.exit(f"ERROR: URL must be a GitHub URL, got: {url}")
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        sys.exit(f"ERROR: Cannot parse owner/repo from URL: {url}")
    owner, repo = parts[0], parts[1]
    slug = repo.lower().replace("_", "-").replace(".", "-")
    return owner, repo, slug


def next_acw_id() -> str:
    """Scan existing YAMLs and return the next acw-NNNN id."""
    pattern = re.compile(r"acw-(\d{4})")
    max_n = 0
    for yaml_path in PROJECTS_DIR.glob("*.yaml"):
        if yaml_path.name == ".gitkeep":
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            id_val = data.get("id", "")
            m = pattern.fullmatch(id_val)
            if m:
                max_n = max(max_n, int(m.group(1)))
        except Exception:
            pass
    return f"acw-{max_n + 1:04d}"


def fetch_github_metadata(owner: str, repo: str) -> tuple[Optional[str], Optional[str]]:
    """
    Return (name, description) from the GitHub API.
    Returns (None, None) if the token is absent or the request fails.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None, None

    try:
        import httpx

        resp = httpx.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("name"), data.get("description")
        else:
            print(
                f"  [warn] GitHub API returned {resp.status_code} — skipping metadata fetch.",
                file=sys.stderr,
            )
    except Exception as exc:
        print(f"  [warn] Could not fetch GitHub metadata: {exc}", file=sys.stderr)

    return None, None


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def prompt_str(label: str, default: Optional[str] = None) -> str:
    default_hint = f" [{default}]" if default else ""
    value = input(f"  {label}{default_hint}: ").strip()
    return value if value else (default or "")


def prompt_list(label: str, hint: str = "") -> list[str]:
    """Prompt for a comma-separated list, returning a Python list of stripped strings."""
    hint_str = f" ({hint})" if hint else ""
    raw = input(f"  {label}{hint_str}: ").strip()
    if not raw:
        return []
    return [v.strip() for v in raw.split(",") if v.strip()]


def prompt_enum(label: str, choices: list[str], nullable: bool = True) -> Optional[str]:
    choices_str = "/".join(choices)
    nullable_hint = "/null" if nullable else ""
    while True:
        raw = input(f"  {label} [{choices_str}{nullable_hint}]: ").strip().lower()
        if raw in ("", "null", "none") and nullable:
            return None
        if raw in choices:
            return raw
        print(f"    Invalid choice. Options: {choices_str}{nullable_hint}")


def prompt_bool(label: str) -> Optional[bool]:
    while True:
        raw = input(f"  {label} [true/false/null]: ").strip().lower()
        if raw in ("", "null", "none"):
            return None
        if raw in ("true", "yes", "y", "1"):
            return True
        if raw in ("false", "no", "n", "0"):
            return False
        print("    Please enter true, false, or null.")


# ---------------------------------------------------------------------------
# YAML construction
# ---------------------------------------------------------------------------

def build_yaml_data(
    *,
    acw_id: str,
    name: str,
    description: str,
    github_url: str,
    disability_area: list[str],
    modality: Optional[str],
    build_docs_quality: str,
    skill_level: Optional[str],
    cost_range: Optional[str],
    nothing_about_us: Optional[bool],
    bom_present: Optional[bool],
) -> dict:
    today = date.today().isoformat()
    data: dict = {
        "id": acw_id,
        "name": name,
        "description": description,
        "added_date": today,
        "tags": [],
        "disability_area": disability_area,
        "modality": modality,
        "user_context": [],
        "interface": [],
        "bom_present": bom_present,
        "build_docs_quality": build_docs_quality,
        "cost_range": cost_range,
        "fabrication_methods": [],
        "skill_level": skill_level,
        "nothing_about_us": nothing_about_us,
        "replicated_by_disabled_person": None,
        "end_user_docs": None,
        "feedback_channel": None,
        "known_deployed_instances": None,
        "license": None,
        "associated_publication": None,
        "institutional_affiliation": None,
        "origin_program": None,
        "documentation_languages": ["en"],
        "sources": [
            {
                "platform": "github",
                "url": github_url,
                "fetched_at": None,
                "stars": None,
                "forks": None,
                "last_commit": None,
                "open_issues": None,
                "open_prs": None,
                "issue_response_rate": None,
                "release_in_last_year": None,
                "readme_has_installation": None,
                "readme_has_usage": None,
                "readme_has_bom": None,
                "release_artifact_present": None,
                "dependencies_pinned": None,
                "has_contributing": None,
                "has_code_of_conduct": None,
                "has_issue_templates": None,
            }
        ],
        "health_tier": None,
        "health_score": None,
    }
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new project YAML file for Assistive Commons Watch."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="GitHub repository URL, e.g. https://github.com/OptiKey/OptiKey",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="Override the derived filename slug (without .yaml extension).",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip interactive prompts; write all curated fields as null.",
    )
    args = parser.parse_args()

    # Normalise URL (strip trailing slashes/git suffix)
    github_url = args.url.rstrip("/").removesuffix(".git")

    # Parse URL
    owner, repo, default_slug = parse_github_url(github_url)
    slug = args.slug if args.slug else default_slug

    # Check destination doesn't already exist
    dest = PROJECTS_DIR / f"{slug}.yaml"
    if dest.exists():
        sys.exit(
            f"ERROR: {dest} already exists. "
            "Use --slug to choose a different filename, or remove the existing file."
        )

    # Assign ID
    acw_id = next_acw_id()

    # Fetch GitHub metadata if possible
    gh_name, gh_description = None, None
    if not args.no_prompt:
        gh_name, gh_description = fetch_github_metadata(owner, repo)
        if gh_name:
            print(f"  Fetched from GitHub API: name='{gh_name}', description='{gh_description}'")

    # Determine field values
    if args.no_prompt:
        name = repo
        description = ""
        disability_area: list[str] = []
        modality: Optional[str] = Modality.software.value
        build_docs_quality = BuildDocsQuality.none.value
        skill_level: Optional[str] = None
        cost_range: Optional[str] = None
        nothing_about_us: Optional[bool] = None
        bom_present: Optional[bool] = None
    else:
        print(f"\nScaffolding project: {github_url}")
        print(f"  Assigned ID : {acw_id}")
        print(f"  Output file : {dest}")
        print()
        print("Fill in the manually curated fields. Press Enter to leave a field null/empty.")
        print()

        name = prompt_str("name", default=gh_name or repo)
        description = prompt_str("description", default=gh_description or "")

        print()
        print("  disability_area — comma-separated list of applicable areas.")
        print("  Common values: motor, eyegaze, communication, hearing, vision, cognitive")
        disability_area = prompt_list("disability_area", hint="comma-separated")

        modality_raw = prompt_enum(
            "modality",
            choices=[m.value for m in Modality],
            nullable=False,
        )
        modality = modality_raw if modality_raw else Modality.software.value

        build_docs_quality_raw = prompt_enum(
            "build_docs_quality",
            choices=[b.value for b in BuildDocsQuality],
            nullable=False,
        )
        build_docs_quality = build_docs_quality_raw if build_docs_quality_raw else BuildDocsQuality.none.value

        skill_level = prompt_enum(
            "skill_level",
            choices=[s.value for s in SkillLevel],
            nullable=True,
        )

        cost_range_raw = input("  cost_range (free text, e.g. '$50-$200', or Enter for null): ").strip()
        cost_range = cost_range_raw if cost_range_raw else None

        nothing_about_us = prompt_bool("nothing_about_us")
        bom_present = prompt_bool("bom_present")

    # Build and validate data before writing
    data = build_yaml_data(
        acw_id=acw_id,
        name=name,
        description=description,
        github_url=github_url,
        disability_area=disability_area,
        modality=modality,
        build_docs_quality=build_docs_quality,
        skill_level=skill_level,
        cost_range=cost_range,
        nothing_about_us=nothing_about_us,
        bom_present=bom_present,
    )

    try:
        from _fetchers.models import Project

        Project.model_validate(data)
    except Exception as exc:
        sys.exit(f"ERROR: Generated data failed validation: {exc}\nData: {data}")

    yaml_text = yaml.dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    dest.write_text(yaml_text, encoding="utf-8")

    print(f"\nWrote {dest}")
    print()
    print("Next steps:")
    print("  python scripts/validate_yaml.py")
    print("  python scripts/build_json.py")


if __name__ == "__main__":
    main()
