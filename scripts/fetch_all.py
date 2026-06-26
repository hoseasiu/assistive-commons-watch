#!/usr/bin/env python3
"""
Fetch live data for all projects and write results back to YAML.

GitHub projects: fetches live API data then recomputes health score/tier.
Printables projects: fetches live GraphQL data then recomputes health score/tier.
Hackaday projects: fetches live API data (requires HACKADAY_API_KEY env var) then recomputes health score/tier.
Static-platform projects (Instructables, Thingiverse, MyMiniFactory):
  live fetching is not yet implemented; health score/tier is recomputed from existing YAML data.

After writing YAMLs, regenerates site/_data/acw.json via build_json.

Usage:
    python scripts/fetch_all.py                      # all projects
    python scripts/fetch_all.py --project acw-0001   # single project

Requires GITHUB_TOKEN env var for authenticated GitHub rate limits (5000 req/hr vs 60).
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Ensure UTF-8 output on Windows so status symbols (✓ ✗ …) render correctly.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from _fetchers.github import GitHubFetcher
from _fetchers.hackaday import HackadayFetcher
from _fetchers.models import Project, Source
from _fetchers.printables import PrintablesFetcher
from _fetchers.scoring import compute_health

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "_data" / "projects"


def _source_to_dict(source: Source) -> dict:
    """Convert any Source model to a plain dict safe for yaml.dump."""
    d = source.model_dump()
    for key, val in d.items():
        if isinstance(val, datetime):
            d[key] = val.isoformat()
    return d


def fetch_project(
    yaml_path: Path,
    github_fetcher: GitHubFetcher,
    hackaday_fetcher: HackadayFetcher | None,
    printables_fetcher: PrintablesFetcher,
) -> tuple[str, str | None, bool]:
    """
    Process one project: fetch live data if it has a GitHub, Hackaday, or Printables
    source, then compute and write back health score/tier.

    Returns (project_id, tier_change_string | None, live_fetch_performed).
    Raises PermissionError on rate-limit, ValueError on bad data.
    """
    raw: dict = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    project = Project.model_validate(raw)

    old_tier = project.health_tier
    live_fetch = False

    for s in project.sources:
        if s.platform == "github":
            url = s.url
            fetched = github_fetcher.fetch(url)
            live_fetch = True

            if fetched.url != url:
                print(f"    URL updated: {url} → {fetched.url}")

            idx = next(
                i for i, src in enumerate(raw.get("sources", []))
                if src.get("platform") == "github"
            )
            raw["sources"][idx] = _source_to_dict(fetched)
            project = Project.model_validate(raw)

        elif s.platform == "hackaday" and hackaday_fetcher is not None:
            url = s.url
            fetched = hackaday_fetcher.fetch(url)
            live_fetch = True

            if fetched.url != url:
                print(f"    URL updated: {url} → {fetched.url}")

            idx = next(
                i for i, src in enumerate(raw.get("sources", []))
                if src.get("platform") == "hackaday"
            )
            raw["sources"][idx] = _source_to_dict(fetched)
            project = Project.model_validate(raw)

        elif s.platform == "printables":
            url = s.url
            fetched = printables_fetcher.fetch(url)
            live_fetch = True

            idx = next(
                i for i, src in enumerate(raw.get("sources", []))
                if src.get("platform") == "printables"
            )
            raw["sources"][idx] = _source_to_dict(fetched)
            project = Project.model_validate(raw)

    score, tier = compute_health(project)
    raw["health_score"] = score
    raw["health_tier"] = tier.value

    yaml_path.write_text(
        yaml.dump(raw, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    tier_change = None
    if old_tier is not None and old_tier != tier:
        tier_change = f"{old_tier.value} → {tier.value}"

    return project.id, tier_change, live_fetch


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
    print(f"Processing {len(yaml_paths)} project(s)…\n")

    processed_count = 0
    live_count = 0
    errors: list[str] = []
    tier_changes: list[str] = []

    try:
        hackaday_fetcher: HackadayFetcher | None = HackadayFetcher()
    except EnvironmentError as exc:
        print(f"Note: {exc} — Hackaday projects will be scored from existing data.\n")
        hackaday_fetcher = None

    try:
        with GitHubFetcher() as github_fetcher, PrintablesFetcher() as printables_fetcher:
            for yaml_path in yaml_paths:
                try:
                    project_id, tier_change, live_fetch = fetch_project(
                        yaml_path, github_fetcher, hackaday_fetcher, printables_fetcher
                    )
                    processed_count += 1
                    if live_fetch:
                        live_count += 1
                        status = f"  ✓ {project_id}"
                    else:
                        status = f"  ~ {project_id}  [scored]"
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
    finally:
        if hackaday_fetcher is not None:
            hackaday_fetcher.__exit__(None, None, None)

    scored_count = processed_count - live_count
    print(f"\nDone — {processed_count} processed ({live_count} live fetched, {scored_count} scored from existing data), {len(errors)} errors")

    if tier_changes:
        print("\nTier changes:")
        for line in tier_changes:
            print(line)

    if errors:
        print(f"\nFailed: {', '.join(errors)}", file=sys.stderr)

    if processed_count > 0:
        print("\nRegenerating site/_data/acw.json…")
        import subprocess
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_json.py")],
            check=True,
        )

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
