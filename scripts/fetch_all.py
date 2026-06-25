#!/usr/bin/env python3
"""
Fetch live GitHub data for all projects and write results back to YAML.

After writing YAMLs, regenerates site/_data/acw.json via build_json.

Usage:
    python scripts/fetch_all.py                      # all projects
    python scripts/fetch_all.py --project acw-0001   # single project

Requires GITHUB_TOKEN env var for authenticated rate limits (5000 req/hr vs 60).
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from _fetchers.github import GitHubFetcher
from _fetchers.models import GitHubSource, Project
from _fetchers.scoring import compute_health

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "_data" / "projects"


def _source_to_dict(source: GitHubSource) -> dict:
    """Convert a GitHubSource to a plain dict safe for yaml.dump."""
    d = source.model_dump()
    if d.get("fetched_at") is not None:
        d["fetched_at"] = d["fetched_at"].isoformat()
    if d.get("last_commit") is not None:
        d["last_commit"] = str(d["last_commit"])
    return d


def fetch_project(yaml_path: Path, fetcher: GitHubFetcher) -> tuple[str, str | None]:
    """
    Fetch live data for one project and write it back to the YAML file.

    Returns (project_id, tier_change_string | None).
    tier_change_string is set only when the tier actually changes.
    Raises PermissionError on rate-limit, ValueError on bad data.
    """
    raw: dict = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    project = Project.model_validate(raw)

    github_sources = [s for s in project.sources if s.platform == "github"]
    if not github_sources:
        print(f"  {project.id}: no GitHub source — skipped")
        return project.id, None

    old_tier = project.health_tier
    url = github_sources[0].url

    fetched = fetcher.fetch(url)

    # Replace the github source in the raw dict in-place (preserves key order).
    github_idx = next(
        i for i, s in enumerate(raw.get("sources", []))
        if s.get("platform") == "github"
    )
    raw["sources"][github_idx] = _source_to_dict(fetched)

    # Revalidate with the live data and compute health.
    updated = Project.model_validate(raw)
    score, tier = compute_health(updated)

    raw["health_score"] = score
    raw["health_tier"] = tier.value

    yaml_path.write_text(
        yaml.dump(raw, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    tier_change = None
    if old_tier is not None and old_tier != tier:
        tier_change = f"{old_tier.value} → {tier.value}"

    return project.id, tier_change


def resolve_yaml_paths(project_id: str | None) -> list[Path]:
    all_paths = sorted(p for p in DATA_DIR.glob("*.yaml") if p.name != ".gitkeep")
    if project_id is None:
        return all_paths

    for path in all_paths:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw.get("id") == project_id:
            return [path]

    print(f"Error: no project found with id {project_id!r}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", metavar="ID", help="Fetch only this project (e.g. acw-0001)")
    args = parser.parse_args()

    yaml_paths = resolve_yaml_paths(args.project)
    print(f"Fetching {len(yaml_paths)} project(s)…\n")

    fetched_count = 0
    errors: list[str] = []
    tier_changes: list[str] = []

    with GitHubFetcher() as fetcher:
        for yaml_path in yaml_paths:
            try:
                project_id, tier_change = fetch_project(yaml_path, fetcher)
                fetched_count += 1
                status = f"  ✓ {project_id}"
                if tier_change:
                    status += f"  [{tier_change}]"
                    tier_changes.append(f"  {project_id}: {tier_change}")
                print(status)
            except PermissionError as exc:
                print(f"  ✗ {yaml_path.stem}: rate-limited — {exc}", file=sys.stderr)
                errors.append(yaml_path.stem)
                break  # no point continuing once rate-limited
            except Exception as exc:
                print(f"  ✗ {yaml_path.stem}: {exc}", file=sys.stderr)
                errors.append(yaml_path.stem)

    print(f"\nDone — fetched {fetched_count}, errors {len(errors)}")

    if tier_changes:
        print("\nTier changes:")
        for line in tier_changes:
            print(line)

    if errors:
        print(f"\nFailed: {', '.join(errors)}", file=sys.stderr)

    # Regenerate acw.json so the site reflects live data.
    if fetched_count > 0:
        print("\nRegenerating site/_data/acw.json…")
        import subprocess
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_json.py")],
            check=True,
        )

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
