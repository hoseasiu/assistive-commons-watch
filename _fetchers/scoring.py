from __future__ import annotations

from datetime import date
from typing import Optional, Union

from .models import (
    BuildDocsQuality,
    GitHubSource,
    HackadaySource,
    HealthTier,
    InstructablesSource,
    MaturityLevel,
    MyMiniFactorySource,
    PrintablesSource,
    Project,
    ThingiverseSource,
)

SCORING_VERSION = "2.0"

_OSI_LICENSES = {
    "MIT", "Apache-2.0",
    "GPL-2.0", "GPL-2.0-only", "GPL-3.0", "GPL-3.0-only",
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-3.0", "LGPL-3.0-only",
    "BSD-2-Clause", "BSD-3-Clause",
    "MPL-2.0", "AGPL-3.0", "AGPL-3.0-only",
    "ISC", "CC0-1.0", "EUPL-1.2", "CERN-OHL-S-2.0", "CERN-OHL-W-2.0",
}

# Supplementary open licenses not in OSI list but freely usable for AT projects
_OPEN_LICENSES = _OSI_LICENSES | {
    "SIL-OFL-1.1", "OFL-1.1",
    "CC-BY-4.0", "CC-BY-SA-4.0",
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
# GitHub scoring (internal 0–10)
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
# Hackaday scoring (internal 0–10)
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
# Shared dimensions (internal 0–10)
# ---------------------------------------------------------------------------

def _at_specific(project: Project) -> float:
    return min(
        10.0,
        (4.0 if project.nothing_about_us else 0.0)
        + (3.0 if project.end_user_docs else 0.0)
        + (2.0 if project.feedback_channel else 0.0)
        + (1.0 if project.known_deployed_instances else 0.0),
    )


def _is_open_license(project: Project, source=None) -> bool:
    spdx = getattr(source, "license_spdx", None)
    cc = getattr(source, "license_cc", None)
    hd = getattr(source, "license", None)
    lic = project.license or spdx or cc or hd
    return lic in _OPEN_LICENSES


def _provenance(
    project: Project,
    source: Optional[GitHubSource | HackadaySource | _StaticSource] = None,
) -> float:
    return min(
        10.0,
        (4.0 if _is_open_license(project, source) else 0.0)
        + (3.0 if project.associated_publication else 0.0)
        + (2.0 if project.institutional_affiliation else 0.0)
        + (1.0 if project.origin_program else 0.0),
    )


# ---------------------------------------------------------------------------
# Maturity inference
# ---------------------------------------------------------------------------

def _is_mature(project: Project, source=None) -> bool:
    if project.maturity == MaturityLevel.mature:
        return True
    if project.maturity == MaturityLevel.active:
        return False
    # Infer from signals
    has_release = getattr(source, "release_artifact_present", False)
    good_docs = project.build_docs_quality in (BuildDocsQuality.partial, BuildDocsQuality.complete)
    open_license = _is_open_license(project, source)
    last_commit = getattr(source, "last_commit", None) or getattr(source, "last_log_date", None)
    if last_commit:
        days = (date.today() - last_commit).days
        right_age = 90 <= days <= 1825
    else:
        right_age = False
    return bool(has_release and good_docs and open_license and right_age)


# ---------------------------------------------------------------------------
# Availability and Momentum (1–5 scale)
# ---------------------------------------------------------------------------

def _availability(project: Project, source, mature: bool) -> float:
    if isinstance(source, GitHubSource):
        rep = _replicability_github(project, source)
    elif isinstance(source, HackadaySource):
        rep = _replicability_hackaday(project, source)
    elif source is not None:
        rep = _replicability_static(project, source)
    else:
        rep = 0.0

    at = _at_specific(project)
    prov = _provenance(project, source)
    mat_bonus = 10.0 if mature else 0.0  # in 0–10 space

    raw = (
        0.40 * rep
        + 0.30 * at
        + 0.20 * prov
        + 0.10 * mat_bonus
    )
    return round(max(1.0, min(5.0, 1.0 + (raw / 10.0) * 4.0)), 2)


def _momentum_github(source: GitHubSource) -> float:
    act = _activity_github(source)
    com = _community_github(source)
    raw = 0.55 * act + 0.45 * com
    return round(max(1.0, min(5.0, 1.0 + (raw / 10.0) * 4.0)), 2)


def _momentum_hackaday(source: HackadaySource) -> float:
    act = _activity_hackaday(source)
    com = _community_hackaday(source)
    raw = 0.55 * act + 0.45 * com
    return round(max(1.0, min(5.0, 1.0 + (raw / 10.0) * 4.0)), 2)


# ---------------------------------------------------------------------------
# Tier assignment
# ---------------------------------------------------------------------------

def _assign_tier(
    availability: float,
    momentum: Optional[float],
    mature: bool,
    activity_raw: float,
    last_commit_or_log,
) -> HealthTier:
    stale = last_commit_or_log and (date.today() - last_commit_or_log).days > 1095
    if activity_raw == 0.0 and stale:
        return HealthTier.archived
    if availability >= 4.0 and momentum is not None and momentum >= 4.0:
        return HealthTier.thriving
    if availability >= 3.0 and momentum is not None and momentum >= 2.5:
        return HealthTier.stable
    if availability >= 3.0 and mature and (momentum is None or momentum < 2.5):
        return HealthTier.complete
    if availability >= 3.0 and (momentum is None or momentum < 2.5):
        return HealthTier.dormant
    if momentum is None:
        return HealthTier.documented
    return HealthTier.at_risk


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_health(project: Project) -> tuple[float, Optional[float], HealthTier]:
    """Compute (availability 1–5, momentum 1–5 or None, tier) for a project."""
    github = next((s for s in project.sources if s.platform == "github"), None)
    hackaday = next((s for s in project.sources if s.platform == "hackaday"), None)
    static = next((s for s in project.sources if s.platform in _STATIC_PLATFORMS), None)

    if github is not None:
        mature = _is_mature(project, github)
        activity_raw = _activity_github(github)
        availability = _availability(project, github, mature)
        momentum = _momentum_github(github)
        tier = _assign_tier(availability, momentum, mature, activity_raw, github.last_commit)
        return availability, momentum, tier

    if hackaday is not None:
        mature = _is_mature(project, hackaday)
        activity_raw = _activity_hackaday(hackaday)
        availability = _availability(project, hackaday, mature)
        momentum = _momentum_hackaday(hackaday)
        tier = _assign_tier(availability, momentum, mature, activity_raw, hackaday.last_log_date)
        return availability, momentum, tier

    if static is not None:
        mature = _is_mature(project, static)
        availability = _availability(project, static, mature)
        return availability, None, HealthTier.documented

    return 1.0, None, HealthTier.unverified


def compute_sub_scores(project: Project) -> dict[str, float | None | bool]:
    """Per-dimension scores — internal 0–10 sub-scores plus top-level 1–5 scores."""
    github = next((s for s in project.sources if s.platform == "github"), None)
    hackaday = next((s for s in project.sources if s.platform == "hackaday"), None)
    static = next((s for s in project.sources if s.platform in _STATIC_PLATFORMS), None)

    if github is not None:
        fetched = github.fetched_at is not None
        mature = _is_mature(project, github)
        availability = _availability(project, github, mature)
        momentum = _momentum_github(github) if fetched else None
        return {
            "availability": availability,
            "momentum": momentum,
            "activity": round(_activity_github(github), 1) if fetched else None,
            "replicability": round(_replicability_github(project, github), 1),
            "community": round(_community_github(github), 1) if fetched else None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, github), 1),
            "mature": mature,
        }

    if hackaday is not None:
        fetched = hackaday.fetched_at is not None
        mature = _is_mature(project, hackaday)
        availability = _availability(project, hackaday, mature)
        momentum = _momentum_hackaday(hackaday) if fetched else None
        return {
            "availability": availability,
            "momentum": momentum,
            "activity": round(_activity_hackaday(hackaday), 1) if fetched else None,
            "replicability": round(_replicability_hackaday(project, hackaday), 1),
            "community": round(_community_hackaday(hackaday), 1) if fetched else None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, hackaday), 1),
            "mature": mature,
        }

    if static is not None:
        mature = _is_mature(project, static)
        availability = _availability(project, static, mature)
        return {
            "availability": availability,
            "momentum": None,
            "activity": round(_activity_static(static), 1),
            "replicability": round(_replicability_static(project, static), 1),
            "community": None,
            "at_specific": round(_at_specific(project), 1),
            "provenance": round(_provenance(project, static), 1),
            "mature": mature,
        }

    return {
        "availability": 1.0,
        "momentum": None,
        "activity": None,
        "replicability": None,
        "community": None,
        "at_specific": round(_at_specific(project), 1),
        "provenance": round(_provenance(project, None), 1),
        "mature": _is_mature(project),
    }
