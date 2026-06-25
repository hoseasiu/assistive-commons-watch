"""Tests for _fetchers/scoring.py — scoring dimensions and tier assignment."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from _fetchers.models import BuildDocsQuality, GitHubSource, HealthTier, Project
from _fetchers.scoring import (
    _activity,
    _at_specific,
    _community,
    _provenance,
    _replicability,
    compute_health,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _source(**kwargs) -> GitHubSource:
    defaults = {"platform": "github", "url": "https://github.com/owner/repo"}
    defaults.update(kwargs)
    return GitHubSource(**defaults)


def _project(**kwargs) -> Project:
    defaults = {
        "id": "acw-0001",
        "name": "Test",
        "description": "Test project",
        "added_date": "2024-01-01",
        "modality": "software",
    }
    defaults.update(kwargs)
    return Project(**defaults)


def _days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


# ---------------------------------------------------------------------------
# _activity
# ---------------------------------------------------------------------------

class TestActivity:
    def test_no_data_returns_zero(self):
        src = _source()
        assert _activity(src) == 0.0

    def test_commit_today_scores_10(self):
        src = _source(last_commit=date.today())
        # 0 days -> 10.0 commit pts, no issue_response_rate, no release
        assert _activity(src) == 10.0

    def test_commit_within_30_days(self):
        src = _source(last_commit=_days_ago(15))
        assert _activity(src) == 9.0

    def test_commit_within_90_days(self):
        src = _source(last_commit=_days_ago(60))
        assert _activity(src) == 7.0

    def test_commit_within_180_days(self):
        src = _source(last_commit=_days_ago(120))
        assert _activity(src) == 5.0

    def test_commit_within_365_days(self):
        src = _source(last_commit=_days_ago(200))
        assert _activity(src) == 3.0

    def test_commit_within_730_days(self):
        src = _source(last_commit=_days_ago(400))
        assert _activity(src) == 1.0

    def test_commit_over_730_days_scores_zero(self):
        src = _source(last_commit=_days_ago(800))
        assert _activity(src) == 0.0

    def test_issue_response_rate_adds_score(self):
        # response_rate=1.0 -> min(3.0, 1.0*3.34) = 3.0
        src = _source(issue_response_rate=1.0)
        assert _activity(src) == pytest.approx(3.0, abs=0.01)

    def test_issue_response_rate_capped_at_3(self):
        src = _source(issue_response_rate=1.0)
        score = _activity(src)
        assert score <= 3.0

    def test_release_in_last_year_adds_2(self):
        src = _source(release_in_last_year=True)
        assert _activity(src) == pytest.approx(2.0)

    def test_all_signals_capped_at_10(self):
        src = _source(
            last_commit=date.today(),   # 10 pts
            issue_response_rate=1.0,    # 3 pts
            release_in_last_year=True,  # 2 pts
        )
        assert _activity(src) == 10.0


# ---------------------------------------------------------------------------
# _replicability
# ---------------------------------------------------------------------------

class TestReplicability:
    def test_no_signals_returns_zero(self):
        p = _project()
        src = _source()
        assert _replicability(p, src) == 0.0

    def test_bom_present_adds_2(self):
        p = _project(bom_present=True)
        src = _source()
        assert _replicability(p, src) == 2.0

    def test_build_docs_partial_adds_2(self):
        p = _project(build_docs_quality=BuildDocsQuality.partial)
        src = _source()
        assert _replicability(p, src) == 2.0

    def test_build_docs_complete_adds_4(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete)
        src = _source()
        assert _replicability(p, src) == 4.0

    def test_dependencies_pinned_adds_1(self):
        p = _project()
        src = _source(dependencies_pinned=True)
        assert _replicability(p, src) == 1.0

    def test_release_artifact_present_adds_2(self):
        p = _project()
        src = _source(release_artifact_present=True)
        assert _replicability(p, src) == 2.0

    def test_readme_install_and_usage_adds_1(self):
        p = _project()
        src = _source(readme_has_installation=True, readme_has_usage=True)
        assert _replicability(p, src) == 1.0

    def test_readme_install_only_adds_nothing(self):
        p = _project()
        src = _source(readme_has_installation=True, readme_has_usage=False)
        assert _replicability(p, src) == 0.0

    def test_all_signals_capped_at_10(self):
        p = _project(
            bom_present=True,                              # +2
            build_docs_quality=BuildDocsQuality.complete,  # +4
        )
        src = _source(
            dependencies_pinned=True,       # +1
            release_artifact_present=True,  # +2
            readme_has_installation=True,   # +1 (both needed)
            readme_has_usage=True,
        )
        # total = 10; all signals sum to exactly 10
        assert _replicability(p, src) == 10.0


# ---------------------------------------------------------------------------
# _community
# ---------------------------------------------------------------------------

class TestCommunity:
    def test_no_signals_returns_zero(self):
        src = _source()
        assert _community(src) == 0.0

    def test_has_contributing_adds_4(self):
        src = _source(has_contributing=True)
        assert _community(src) == 4.0

    def test_has_issue_templates_adds_3(self):
        src = _source(has_issue_templates=True)
        assert _community(src) == 3.0

    def test_has_code_of_conduct_adds_3(self):
        src = _source(has_code_of_conduct=True)
        assert _community(src) == 3.0

    def test_all_signals_returns_10(self):
        src = _source(has_contributing=True, has_issue_templates=True, has_code_of_conduct=True)
        assert _community(src) == 10.0


# ---------------------------------------------------------------------------
# _at_specific
# ---------------------------------------------------------------------------

class TestAtSpecific:
    def test_no_signals_returns_zero(self):
        p = _project()
        assert _at_specific(p) == 0.0

    def test_nothing_about_us_adds_4(self):
        p = _project(nothing_about_us=True)
        assert _at_specific(p) == 4.0

    def test_end_user_docs_adds_3(self):
        p = _project(end_user_docs=True)
        assert _at_specific(p) == 3.0

    def test_feedback_channel_adds_2(self):
        p = _project(feedback_channel=True)
        assert _at_specific(p) == 2.0

    def test_known_deployed_instances_adds_1(self):
        p = _project(known_deployed_instances="3 schools")
        assert _at_specific(p) == 1.0

    def test_all_signals_returns_10(self):
        p = _project(
            nothing_about_us=True,
            end_user_docs=True,
            feedback_channel=True,
            known_deployed_instances="5 users",
        )
        assert _at_specific(p) == 10.0


# ---------------------------------------------------------------------------
# _provenance
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_no_signals_returns_zero(self):
        p = _project()
        assert _provenance(p) == 0.0

    def test_osi_license_adds_4(self):
        p = _project(license="MIT")
        assert _provenance(p) == 4.0

    def test_non_osi_license_adds_nothing(self):
        p = _project(license="Proprietary")
        assert _provenance(p) == 0.0

    def test_associated_publication_adds_3(self):
        p = _project(associated_publication="doi:10.1234/test")
        assert _provenance(p) == 3.0

    def test_institutional_affiliation_adds_2(self):
        p = _project(institutional_affiliation="MIT")
        assert _provenance(p) == 2.0

    def test_origin_program_adds_1(self):
        p = _project(origin_program="GSoC")
        assert _provenance(p) == 1.0

    def test_all_signals_returns_10(self):
        p = _project(
            license="MIT",
            associated_publication="doi:10.1234/test",
            institutional_affiliation="MIT",
            origin_program="GSoC",
        )
        assert _provenance(p) == 10.0

    def test_various_osi_licenses_pass(self):
        for lic in ["Apache-2.0", "GPL-3.0", "BSD-3-Clause", "AGPL-3.0-only"]:
            p = _project(license=lic)
            assert _provenance(p) == 4.0, f"Expected 4.0 for {lic}"


# ---------------------------------------------------------------------------
# compute_health — tier boundary conditions
# ---------------------------------------------------------------------------

class TestComputeHealthTierBoundaries:
    """
    Tier rules (first match wins):
      archived  : activity == 0.0 AND last_commit > 3 years ago
      thriving  : score >= 7.5
      stable    : score >= 5.5
      dormant   : activity <= 2 AND replicability >= 5
      at_risk   : else
    """

    def test_no_source_returns_unverified(self):
        p = _project()
        score, tier = compute_health(p)
        assert score == 0.0
        assert tier == HealthTier.unverified

    def test_archived_when_activity_zero_and_commit_over_3yr(self):
        p = _project(
            sources=[_source(last_commit=_days_ago(1096))],
        )
        score, tier = compute_health(p)
        assert tier == HealthTier.archived

    def test_not_archived_when_commit_exactly_3yr(self):
        # Exactly 1095 days — stale condition requires > 1095
        p = _project(sources=[_source(last_commit=_days_ago(1095))])
        score, tier = compute_health(p)
        assert tier != HealthTier.archived

    def test_thriving_when_score_gte_75(self):
        # Build a project that scores >= 7.5
        # Max score components: activity=10, replicability=10, community=10, at_specific=10, provenance=10
        # Weighted: 0.25*10 + 0.30*10 + 0.15*10 + 0.20*10 + 0.10*10 = 10.0
        p = _project(
            bom_present=True,
            build_docs_quality=BuildDocsQuality.complete,
            nothing_about_us=True,
            end_user_docs=True,
            feedback_channel=True,
            known_deployed_instances="5 users",
            license="MIT",
            associated_publication="doi:10.1234/test",
            institutional_affiliation="MIT",
            origin_program="GSoC",
            sources=[_source(
                last_commit=date.today(),
                issue_response_rate=1.0,
                release_in_last_year=True,
                dependencies_pinned=True,
                release_artifact_present=True,
                readme_has_installation=True,
                readme_has_usage=True,
                has_contributing=True,
                has_issue_templates=True,
                has_code_of_conduct=True,
            )],
        )
        score, tier = compute_health(p)
        assert score >= 7.5
        assert tier == HealthTier.thriving

    def test_stable_when_score_gte_55_lt_75(self):
        # Craft a project that lands between 5.5 and 7.5
        # activity=7 (commit ~60d ago) -> 0.25*7=1.75
        # replicability=6 (complete docs+pinned) -> 0.30*6=1.80
        # community=10 (all) -> 0.15*10=1.50
        # at_specific=0 -> 0
        # provenance=4 (MIT) -> 0.10*4=0.40
        # total = 1.75+1.80+1.50+0+0.40 = 5.45 -- slightly off; adjust
        # Use complete docs (4) + artifact (2) + readme (1) = 7 replicability -> 0.30*7=2.10
        # total = 1.75+2.10+1.50+0+0.40 = 5.75 (stable)
        p = _project(
            build_docs_quality=BuildDocsQuality.complete,
            license="MIT",
            sources=[_source(
                last_commit=_days_ago(60),
                release_artifact_present=True,
                readme_has_installation=True,
                readme_has_usage=True,
                has_contributing=True,
                has_issue_templates=True,
                has_code_of_conduct=True,
            )],
        )
        score, tier = compute_health(p)
        assert 5.5 <= score < 7.5
        assert tier == HealthTier.stable

    def test_dormant_when_low_activity_high_replicability(self):
        # activity <= 2: commit > 730 days (0 pts) + no response_rate + no release
        # replicability >= 5: bom(2) + complete(4) = 6
        p = _project(
            bom_present=True,
            build_docs_quality=BuildDocsQuality.complete,
            sources=[_source(last_commit=_days_ago(800))],
        )
        score, tier = compute_health(p)
        assert tier == HealthTier.dormant

    def test_at_risk_when_low_activity_low_replicability(self):
        # activity=0, replicability=0 -> at_risk
        p = _project(sources=[_source(last_commit=_days_ago(800))])
        score, tier = compute_health(p)
        assert tier == HealthTier.at_risk

    def test_at_risk_when_high_activity_low_score(self):
        # activity=1 (730d commit), replicability=0, everything else 0
        # score = 0.25*1 = 0.25 -> at_risk (not dormant since replicability < 5)
        p = _project(sources=[_source(last_commit=_days_ago(400))])
        score, tier = compute_health(p)
        assert tier == HealthTier.at_risk


# ---------------------------------------------------------------------------
# compute_health — end-to-end with a Project fixture
# ---------------------------------------------------------------------------

class TestComputeHealthEndToEnd:
    def test_returns_float_and_health_tier(self):
        p = _project(sources=[_source(last_commit=date.today())])
        score, tier = compute_health(p)
        assert isinstance(score, float)
        assert isinstance(tier, HealthTier)

    def test_score_within_bounds(self):
        p = _project(sources=[_source(
            last_commit=date.today(),
            issue_response_rate=0.5,
            release_in_last_year=True,
        )])
        score, tier = compute_health(p)
        assert 0.0 <= score <= 10.0

    def test_score_is_rounded_to_2_decimal_places(self):
        p = _project(sources=[_source(
            last_commit=_days_ago(60),  # activity=7
            issue_response_rate=0.5,
        )])
        score, tier = compute_health(p)
        # Should be rounded to 2 decimal places
        assert score == round(score, 2)

    def test_full_project_fixture(self):
        """End-to-end: fully populated project produces expected score and tier."""
        p = _project(
            bom_present=True,
            build_docs_quality=BuildDocsQuality.complete,
            nothing_about_us=True,
            end_user_docs=True,
            feedback_channel=True,
            known_deployed_instances="10 users",
            license="Apache-2.0",
            associated_publication="doi:10.99/x",
            institutional_affiliation="University",
            origin_program="GSoC",
            sources=[_source(
                last_commit=_days_ago(15),      # activity: 9.0 commit
                issue_response_rate=1.0,        # activity: +3.0, capped at 10
                release_in_last_year=True,      # activity: +2.0, capped at 10
                dependencies_pinned=True,
                release_artifact_present=True,
                readme_has_installation=True,
                readme_has_usage=True,
                has_contributing=True,
                has_issue_templates=True,
                has_code_of_conduct=True,
            )],
        )
        score, tier = compute_health(p)
        # All dimensions max out at 10
        # score = 0.25*10 + 0.30*10 + 0.15*10 + 0.20*10 + 0.10*10 = 10.0
        assert score == 10.0
        assert tier == HealthTier.thriving
