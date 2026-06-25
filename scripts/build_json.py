#!/usr/bin/env python3
"""
Build site/_data/acw.json from _data/projects/*.yaml.

Reads every project YAML, uses the stored health_tier/health_score if set
(written by the nightly fetch workflow), otherwise computes them live.
Outputs a pre-aggregated JSON blob that the 11ty Landscape page renders
directly — no runtime computation needed in the template.

Usage:
    python scripts/build_json.py
"""

import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from _fetchers.models import BuildDocsQuality, HealthTier, Project
from _fetchers.scoring import compute_health, compute_sub_scores

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "_data" / "projects"
OUT_PATH = ROOT / "site" / "_data" / "acw.json"

# Canonical display areas — order controls rendering order on the page.
# First disability_area slug in each project's YAML determines which area it
# appears in on the Landscape view.
AREA_DEFS = [
    ("communication", "AAC / Communication"),
    ("eyegaze", "Eye Gaze / Tracking"),
    ("motor", "Motor / Switch Access"),
    ("vision", "Vision / Braille"),
    ("hearing", "Hearing"),
    ("prosthetics", "Prosthetics / Rehab"),
]
AREA_LABEL = {slug: label for slug, label in AREA_DEFS}

TIER_ORDER = [
    HealthTier.thriving,
    HealthTier.stable,
    HealthTier.dormant,
    HealthTier.at_risk,
    HealthTier.archived,
    HealthTier.unverified,
]

TIER_LABELS = {
    "thriving": "Thriving",
    "stable": "Stable",
    "dormant": "Dormant",
    "at_risk": "At Risk",
    "archived": "Archived",
    "unverified": "Unverified",
}

MODALITY_LABELS = {
    "hardware": "Hardware",
    "software": "Software",
    "firmware": "Firmware",
    "hybrid": "Hardware + Software",
}

SKILL_LABELS = {
    "beginner": "Beginner",
    "maker": "Maker / DIY",
    "engineer": "Engineer",
}

BUILD_DOCS_LABELS = {
    "none": "None",
    "partial": "Partial",
    "complete": "Complete",
}


def _generate_summary(sub_scores: dict, project: Project) -> str:
    """Two-sentence plain-language synthesis based on statically-available signals."""
    at_spec = sub_scores["at_specific"]
    replic = sub_scores.get("replicability") or 0.0

    parts = []

    if at_spec >= 7:
        parts.append(
            "Designed with disabled users in mind — end-user docs and feedback channels are present."
        )
    elif project.end_user_docs:
        parts.append("End-user documentation is available.")
    elif not project.end_user_docs and not project.nothing_about_us:
        parts.append("No end-user documentation found — primarily a builder/developer resource.")
    else:
        parts.append("Limited AT-specific user documentation.")

    if replic >= 6:
        parts.append("Well-documented for replication.")
    elif replic >= 3 or project.build_docs_quality == BuildDocsQuality.partial:
        parts.append("Partial build documentation available.")
    elif project.build_docs_quality == BuildDocsQuality.none:
        parts.append("Build documentation is not available — check the repository directly.")

    return " ".join(parts)


def load_projects() -> list[dict]:
    records = []
    for yaml_path in sorted(DATA_DIR.glob("*.yaml")):
        if yaml_path.name == ".gitkeep":
            continue
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        project = Project.model_validate(raw)

        # Use stored tier/score if available (post-fetch); otherwise compute.
        if project.health_tier is not None and project.health_score is not None:
            tier = project.health_tier.value
            score = project.health_score
        else:
            computed_score, computed_tier = compute_health(project)
            tier = computed_tier.value
            score = computed_score

        primary_area = project.disability_area[0] if project.disability_area else "other"

        source = next((s for s in project.sources if s.platform == "github"), None)
        sub_scores = compute_sub_scores(project)
        summary = _generate_summary(sub_scores, project)

        latest_release_url = source.latest_release_url if source else None
        download_ready = bool(
            project.modality.value in ("software", "hybrid") and latest_release_url
        )

        records.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "plain_language_description": project.plain_language_description,
                "added_date": str(project.added_date),
                "primary_area": primary_area,
                "primary_area_label": AREA_LABEL.get(primary_area, primary_area.title()),
                "health_tier": tier,
                "health_tier_label": TIER_LABELS.get(tier, tier),
                "health_score": score,
                "github_url": next(
                    (s.url for s in project.sources if s.platform == "github"), None
                ),
                # Sub-scores and summary (for detail pages)
                "scores": sub_scores,
                "summary": summary,
                # Full metadata
                "tags": project.tags,
                "disability_area": project.disability_area,
                "disability_area_labels": [
                    AREA_LABEL.get(a, a.replace("_", " ").title())
                    for a in project.disability_area
                ],
                "modality": project.modality.value,
                "modality_label": MODALITY_LABELS.get(project.modality.value, project.modality.value),
                "interface": project.interface,
                "user_context": project.user_context,
                "fabrication_methods": project.fabrication_methods,
                "bom_present": project.bom_present,
                "build_docs_quality": project.build_docs_quality.value,
                "build_docs_quality_label": BUILD_DOCS_LABELS.get(
                    project.build_docs_quality.value, project.build_docs_quality.value
                ),
                "skill_level": project.skill_level.value if project.skill_level else None,
                "skill_level_label": SKILL_LABELS.get(
                    project.skill_level.value, project.skill_level.value
                ) if project.skill_level else None,
                "cost_range": project.cost_range,
                "license": project.license,
                "nothing_about_us": project.nothing_about_us,
                "replicated_by_disabled_person": project.replicated_by_disabled_person,
                "end_user_docs": project.end_user_docs,
                "feedback_channel": project.feedback_channel,
                "known_deployed_instances": project.known_deployed_instances,
                "associated_publication": project.associated_publication,
                "institutional_affiliation": project.institutional_affiliation,
                "origin_program": project.origin_program,
                "documentation_languages": project.documentation_languages,
                "platform": project.platform,
                "latest_release_url": latest_release_url,
                "download_ready": download_ready,
                "github_stars": source.stars if source else None,
                "github_forks": source.forks if source else None,
                "github_last_commit": str(source.last_commit) if source and source.last_commit else None,
                "github_open_issues": source.open_issues if source else None,
            }
        )
    return records


def build_tier_counts(projects: list[dict]) -> dict:
    counts = {t.value: 0 for t in TIER_ORDER}
    for p in projects:
        counts[p["health_tier"]] = counts.get(p["health_tier"], 0) + 1
    return counts


def build_by_area(projects: list[dict]) -> list[dict]:
    area_map: dict[str, list[dict]] = {slug: [] for slug, _ in AREA_DEFS}
    for p in projects:
        slug = p["primary_area"]
        if slug in area_map:
            area_map[slug].append(p)

    result = []
    for slug, label in AREA_DEFS:
        area_projects = sorted(
            area_map[slug],
            key=lambda p: TIER_ORDER.index(
                HealthTier(p["health_tier"])
            ) if p["health_tier"] in [t.value for t in TIER_ORDER] else 99,
        )
        active_count = sum(
            1 for p in area_projects
            if p["health_tier"] in ("thriving", "stable")
        )
        result.append(
            {
                "slug": slug,
                "label": label,
                "count": len(area_projects),
                "active_count": active_count,
                "projects": area_projects,
            }
        )
    return result


def build_needs_attention(projects: list[dict]) -> list[dict]:
    """Dormant and at-risk projects, limited to 5, with a short note."""
    attention_tiers = {"dormant", "at_risk"}
    candidates = [p for p in projects if p["health_tier"] in attention_tiers]
    # Sort: at_risk first, then dormant; within each by score ascending (worst first)
    candidates.sort(key=lambda p: (p["health_tier"] != "at_risk", p["health_score"]))
    return candidates[:5]


def build_recently_added(projects: list[dict]) -> list[dict]:
    sorted_by_date = sorted(projects, key=lambda p: p["added_date"], reverse=True)
    return sorted_by_date[:5]


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    projects = load_projects()
    tier_counts = build_tier_counts(projects)
    by_area = build_by_area(projects)

    active_count = tier_counts.get("thriving", 0) + tier_counts.get("stable", 0)
    total = len(projects)
    active_pct = round(active_count / total * 100) if total else 0
    dormant_count = tier_counts.get("dormant", 0)
    area_count = sum(1 for a in by_area if a["count"] > 0)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "last_refreshed": str(date.today()),
        "stats": {
            "total": total,
            "areas": area_count,
            "active_or_better_pct": active_pct,
            "dormant_count": dormant_count,
        },
        "tier_counts": tier_counts,
        "by_area": by_area,
        "needs_attention": build_needs_attention(projects),
        "recently_added": build_recently_added(projects),
        "projects": projects,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {total} projects to {OUT_PATH}")
    print(
        f"Tiers: "
        + ", ".join(f"{k}={v}" for k, v in tier_counts.items() if v > 0)
    )


if __name__ == "__main__":
    main()
