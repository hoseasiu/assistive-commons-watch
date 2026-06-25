from __future__ import annotations

from datetime import date
from typing import Optional

from .models import BuildDocsQuality, GitHubSource, HealthTier, Project

SCORING_VERSION = "1.0"

_OSI_LICENSES = {
    "MIT", "Apache-2.0",
    "GPL-2.0", "GPL-2.0-only", "GPL-3.0", "GPL-3.0-only",
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-3.0", "LGPL-3.0-only",
    "BSD-2-Clause", "BSD-3-Clause",
    "MPL-2.0", "AGPL-3.0", "AGPL-3.0-only",
    "ISC", "CC0-1.0", "EUPL-1.2", "CERN-OHL-S-2.0", "CERN-OHL-W-2.0",
}

# (max_days_inclusive, score) — ordered; first match wins
_COMMIT_AGE_SCORES: list[tuple[int, float]] = [
    (0, 10.0),
    (30, 9.0),
    (90, 7.0),
    (180, 5.0),
    (365, 3.0),
    (730, 1.0),
]


def _activity(source: GitHubSource) -> float:
    score = 0.0

    if source.last_commit:
        days = (date.today() - source.last_commit).days
        for threshold, pts in _COMMIT_AGE_SCORES:
            if days <= threshold:
                score += pts
                break
        # days > 730 → 0 pts (already 0.0)

    if source.issue_response_rate is not None:
        score += min(3.0, source.issue_response_rate * 3.34)

    if source.release_in_last_year:
        score += 2.0

    return min(10.0, score)


def _replicability(project: Project, source: GitHubSource) -> float:
    score = 0.0

    if project.bom_present:
        score += 2.0

    score += {
        BuildDocsQuality.none: 0.0,
        BuildDocsQuality.partial: 2.0,
        BuildDocsQuality.complete: 4.0,
    }[project.build_docs_quality]

    if source.dependencies_pinned:
        score += 1.0
    if source.release_artifact_present:
        score += 2.0
    if source.readme_has_installation and source.readme_has_usage:
        score += 1.0

    return min(10.0, score)


def _community(source: GitHubSource) -> float:
    return min(
        10.0,
        (4.0 if source.has_contributing else 0.0)
        + (3.0 if source.has_issue_templates else 0.0)
        + (3.0 if source.has_code_of_conduct else 0.0),
    )


def _at_specific(project: Project) -> float:
    return min(
        10.0,
        (4.0 if project.nothing_about_us else 0.0)
        + (3.0 if project.end_user_docs else 0.0)
        + (2.0 if project.feedback_channel else 0.0)
        + (1.0 if project.known_deployed_instances else 0.0),
    )


def _provenance(project: Project, source: Optional[GitHubSource] = None) -> float:
    lic = project.license or (source.license_spdx if source is not None else None)
    return min(
        10.0,
        (4.0 if lic in _OSI_LICENSES else 0.0)
        + (3.0 if project.associated_publication else 0.0)
        + (2.0 if project.institutional_affiliation else 0.0)
        + (1.0 if project.origin_program else 0.0),
    )


def compute_health(project: Project) -> tuple[float, HealthTier]:
    """Compute (score 0–10, tier) for a project. Does not mutate the project."""
    source = next((s for s in project.sources if s.platform == "github"), None)

    if source is None:
        return 0.0, HealthTier.unverified

    activity = _activity(source)
    replicability = _replicability(project, source)
    community = _community(source)
    at_specific = _at_specific(project)
    provenance = _provenance(project, source)

    score = round(
        0.25 * activity
        + 0.30 * replicability
        + 0.15 * community
        + 0.20 * at_specific
        + 0.10 * provenance,
        2,
    )

    # Tier rules — first match wins
    stale = source.last_commit and (date.today() - source.last_commit).days > 1095
    if activity == 0.0 and stale:
        tier = HealthTier.archived
    elif score >= 7.5:
        tier = HealthTier.thriving
    elif score >= 5.5:
        tier = HealthTier.stable
    elif activity <= 2.0 and replicability >= 5.0:
        tier = HealthTier.dormant
    else:
        tier = HealthTier.at_risk

    return score, tier


def compute_sub_scores(project: Project) -> dict[str, float | None]:
    """Per-dimension scores from available data.

    activity and community return None when fetched_at is null — those
    dimensions require live GitHub API data and can't be estimated statically.
    """
    source = next((s for s in project.sources if s.platform == "github"), None)

    if source is None:
        return {
            "activity": None,
            "replicability": None,
            "community": None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, None), 1),
        }

    fetched = source.fetched_at is not None
    return {
        "activity": round(_activity(source), 1) if fetched else None,
        "replicability": round(_replicability(project, source), 1),
        "community": round(_community(source), 1) if fetched else None,
        "at_specific": round(_at_specific(project), 1),
        "provenance": round(_provenance(project, source), 1),
    }
