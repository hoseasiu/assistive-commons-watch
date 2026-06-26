from __future__ import annotations

from datetime import date
from typing import Optional, Union

from .models import (
    BuildDocsQuality,
    GitHubSource,
    HackadaySource,
    HealthTier,
    InstructablesSource,
    MyMiniFactorySource,
    PrintablesSource,
    Project,
    ThingiverseSource,
)

SCORING_VERSION = "1.1"

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

_StaticSource = Union[
    InstructablesSource, PrintablesSource, ThingiverseSource, MyMiniFactorySource
]

_STATIC_PLATFORMS = {"instructables", "printables", "thingiverse", "myminifactory"}


# ---------------------------------------------------------------------------
# GitHub scoring
# ---------------------------------------------------------------------------

def _activity_github(source: GitHubSource) -> float:
    score = 0.0

    if source.last_commit:
        days = (date.today() - source.last_commit).days
        for threshold, pts in _COMMIT_AGE_SCORES:
            if days <= threshold:
                score += pts
                break

    if source.issue_response_rate is not None:
        score += min(3.0, source.issue_response_rate * 3.34)

    if source.release_in_last_year:
        score += 2.0

    return min(10.0, score)


def _replicability_github(project: Project, source: GitHubSource) -> float:
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


def _community_github(source: GitHubSource) -> float:
    return min(
        10.0,
        (4.0 if source.has_contributing else 0.0)
        + (3.0 if source.has_issue_templates else 0.0)
        + (3.0 if source.has_code_of_conduct else 0.0),
    )


# ---------------------------------------------------------------------------
# Static-platform scoring (Instructables, Printables, Thingiverse, MyMiniFactory)
# ---------------------------------------------------------------------------

def _activity_static(source: _StaticSource) -> float:
    """Floor model: static platforms have no post-publish activity signal."""
    score = 4.0

    published = getattr(source, "published_date", None)
    if published:
        days = (date.today() - published).days
        if days <= 730:
            score += 1.0
        elif days > 1825:
            score -= 1.0

    comments = getattr(source, "comments", None)
    if comments and comments > 20:
        score += 0.5

    return min(5.0, score)  # honest ceiling — no real activity data


def _replicability_static(project: Project, source: _StaticSource) -> float:
    score = 0.0

    bom = (
        project.bom_present
        or getattr(source, "has_bom_step", None)
        or getattr(source, "has_components_list", None)
    )
    if bom:
        score += 2.0

    score += {
        BuildDocsQuality.none: 0.0,
        BuildDocsQuality.partial: 2.0,
        BuildDocsQuality.complete: 4.0,
    }[project.build_docs_quality]

    if getattr(source, "has_download_files", None) or getattr(source, "has_files", None):
        score += 2.0

    makes = (
        getattr(source, "makes_count", None)
        or getattr(source, "imadeit_count", None)
        or getattr(source, "build_count", None)
    )
    if makes and makes > 5:
        score += 1.0

    if (
        getattr(source, "guaranteed_printable", None)
        or getattr(source, "staff_pick", None)
        or getattr(source, "contest_winner", None)
    ):
        score += 0.5

    if getattr(source, "is_free", None) is False:
        score -= 1.0

    return min(10.0, max(0.0, score))


# ---------------------------------------------------------------------------
# Hackaday scoring
# ---------------------------------------------------------------------------

def _activity_hackaday(source: HackadaySource) -> float:
    """Use last_log_date exactly as GitHub uses last_commit."""
    score = 0.0
    if source.last_log_date:
        days = (date.today() - source.last_log_date).days
        for threshold, pts in _COMMIT_AGE_SCORES:
            if days <= threshold:
                score += pts
                break
    return min(10.0, score)


def _replicability_hackaday(project: Project, source: HackadaySource) -> float:
    score = 0.0

    if project.bom_present or source.has_components_list:
        score += 2.0

    score += {
        BuildDocsQuality.none: 0.0,
        BuildDocsQuality.partial: 2.0,
        BuildDocsQuality.complete: 4.0,
    }[project.build_docs_quality]

    if source.has_files:
        score += 2.0

    if source.build_count and source.build_count > 5:
        score += 1.0

    return min(10.0, score)


def _community_hackaday(source: HackadaySource) -> float:
    score = 0.0
    if source.team_size and source.team_size > 1:
        score += 4.0
    if source.followers:
        score += min(3.0, source.followers / 50)
    if source.build_count and source.build_count > 0:
        score += min(3.0, source.build_count / 10)
    return min(10.0, score)


# ---------------------------------------------------------------------------
# Shared dimensions
# ---------------------------------------------------------------------------

def _at_specific(project: Project) -> float:
    return min(
        10.0,
        (4.0 if project.nothing_about_us else 0.0)
        + (3.0 if project.end_user_docs else 0.0)
        + (2.0 if project.feedback_channel else 0.0)
        + (1.0 if project.known_deployed_instances else 0.0),
    )


def _provenance(
    project: Project,
    source: Optional[GitHubSource | HackadaySource | _StaticSource] = None,
) -> float:
    spdx = getattr(source, "license_spdx", None)
    cc = getattr(source, "license_cc", None)
    hd = getattr(source, "license", None)
    lic = project.license or spdx or cc or hd
    return min(
        10.0,
        (4.0 if lic in _OSI_LICENSES else 0.0)
        + (3.0 if project.associated_publication else 0.0)
        + (2.0 if project.institutional_affiliation else 0.0)
        + (1.0 if project.origin_program else 0.0),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_health(project: Project) -> tuple[float, HealthTier]:
    """Compute (score 0–10, tier) for a project. Does not mutate the project."""
    github = next((s for s in project.sources if s.platform == "github"), None)
    hackaday = next((s for s in project.sources if s.platform == "hackaday"), None)
    static = next((s for s in project.sources if s.platform in _STATIC_PLATFORMS), None)

    # GitHub takes precedence for activity and community; Hackaday supplements if no GitHub
    if github is not None:
        activity = _activity_github(github)
        replicability = _replicability_github(project, github)
        community = _community_github(github)
        at_specific = _at_specific(project)
        provenance = _provenance(project, github)

        score = round(
            0.25 * activity
            + 0.30 * replicability
            + 0.15 * community
            + 0.20 * at_specific
            + 0.10 * provenance,
            2,
        )

        stale = github.last_commit and (date.today() - github.last_commit).days > 1095
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

    if hackaday is not None:
        activity = _activity_hackaday(hackaday)
        replicability = _replicability_hackaday(project, hackaday)
        community = _community_hackaday(hackaday)
        at_specific = _at_specific(project)
        provenance = _provenance(project, hackaday)

        score = round(
            0.25 * activity
            + 0.30 * replicability
            + 0.15 * community
            + 0.20 * at_specific
            + 0.10 * provenance,
            2,
        )

        stale = hackaday.last_log_date and (date.today() - hackaday.last_log_date).days > 1095
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

    if static is not None:
        activity = _activity_static(static)
        replicability = _replicability_static(project, static)
        at_specific = _at_specific(project)
        provenance = _provenance(project, static)

        # Community is not scored for static-platform-only projects
        score = round(
            0.25 * activity
            + 0.30 * replicability
            + 0.20 * at_specific
            + 0.10 * provenance,
            2,
        )

        return score, HealthTier.documented

    return 0.0, HealthTier.unverified


def compute_sub_scores(project: Project) -> dict[str, float | None]:
    """Per-dimension scores from available data."""
    github = next((s for s in project.sources if s.platform == "github"), None)
    hackaday = next((s for s in project.sources if s.platform == "hackaday"), None)
    static = next((s for s in project.sources if s.platform in _STATIC_PLATFORMS), None)

    if github is not None:
        fetched = github.fetched_at is not None
        return {
            "activity": round(_activity_github(github), 1) if fetched else None,
            "replicability": round(_replicability_github(project, github), 1),
            "community": round(_community_github(github), 1) if fetched else None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, github), 1),
        }

    if hackaday is not None:
        fetched = hackaday.fetched_at is not None
        return {
            "activity": round(_activity_hackaday(hackaday), 1) if fetched else None,
            "replicability": round(_replicability_hackaday(project, hackaday), 1),
            "community": round(_community_hackaday(hackaday), 1) if fetched else None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, hackaday), 1),
        }

    if static is not None:
        return {
            "activity": round(_activity_static(static), 1),
            "replicability": round(_replicability_static(project, static), 1),
            "community": None,  # not scored for static-platform-only projects
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, static), 1),
        }

    return {
        "activity": None,
        "replicability": None,
        "community": None,
        "at_specific": round(_at_specific(project), 1),
        "provenance": round(_provenance(project, None), 1),
    }
