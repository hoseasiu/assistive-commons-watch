"""Tests for _fetchers/scoring.py — scoring dimensions and tier assignment."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from _fetchers.models import BuildDocsQuality, GitHubSource, HealthTier, MaturityLevel, Project
from _fetchers.scoring import (
    _activity_github,
    _at_specific,
    _community_github,
    _is_mature,
    _momentum_github,
    _provenance,
    _replicability_github,
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
# _activity_github
# ---------------------------------------------------------------------------

class TestActivity:
    def test_no_data_returns_zero(self):
        src = _source()
        assert _activity_github(src) == 0.0

    def test_commit_today_scores_10(self):
        src = _source(last_commit=date.today())
        assert _activity_github(src) == 10.0

    def test_commit_within_30_days(self):
        src = _source(last_commit=_days_ago(15))
        assert _activity_github(src) == 9.0

    def test_commit_within_90_days(self):
        src = _source(last_commit=_days_ago(60))
        assert _activity_github(src) == 7.0

    def test_commit_within_180_days(self):
        src = _source(last_commit=_days_ago(120))
        assert _activity_github(src) == 5.0

    def test_commit_within_365_days(self):
        src = _source(last_commit=_days_ago(200))
        assert _activity_github(src) == 3.0

    def test_commit_within_730_days(self):
        src = _source(last_commit=_days_ago(400))
        assert _activity_github(src) == 1.0

    def test_commit_over_730_days_scores_zero(self):
        src = _source(last_commit=_days_ago(800))
        assert _activity_github(src) == 0.0

    def test_issue_response_rate_adds_score(self):
        src = _source(issue_response_rate=1.0)
        assert _activity_github(src) == pytest.approx(3.0, abs=0.01)

    def test_issue_response_rate_capped_at_3(self):
        src = _source(issue_response_rate=1.0)
        assert _activity_github(src) <= 3.0

    def test_release_in_last_year_adds_2(self):
        src = _source(release_in_last_year=True)
        assert _activity_github(src) == pytest.approx(2.0)

    def test_all_signals_capped_at_10(self):
        src = _source(
            last_commit=date.today(),
            issue_response_rate=1.0,
            release_in_last_year=True,
        )
        assert _activity_github(src) == 10.0


# ---------------------------------------------------------------------------
# _replicability_github
# ---------------------------------------------------------------------------

class TestReplicability:
    def test_no_signals_returns_zero(self):
        p = _project()
        src = _source()
        assert _replicability_github(p, src) == 0.0

    def test_bom_present_adds_2(self):
        p = _project(bom_present=True)
        src = _source()
        assert _replicability_github(p, src) == 2.0

    def test_build_docs_partial_adds_2(self):
        p = _project(build_docs_quality=BuildDocsQuality.partial)
        src = _source()
        assert _replicability_github(p, src) == 2.0

    def test_build_docs_complete_adds_4(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete)
        src = _source()
        assert _replicability_github(p, src) == 4.0

    def test_dependencies_pinned_adds_1(self):
        p = _project()
        src = _source(dependencies_pinned=True)
        assert _replicability_github(p, src) == 1.0

    def test_release_artifact_present_adds_2(self):
        p = _project()
        src = _source(release_artifact_present=True)
        assert _replicability_github(p, src) == 2.0

    def test_readme_install_and_usage_adds_1(self):
        p = _project()
        src = _source(readme_has_installation=True, readme_has_usage=True)
        assert _replicability_github(p, src) == 1.0

    def test_readme_install_only_adds_nothing(self):
        p = _project()
        src = _source(readme_has_installation=True, readme_has_usage=False)
        assert _replicability_github(p, src) == 0.0

    def test_all_signals_capped_at_10(self):
        p = _project(
            bom_present=True,
            build_docs_quality=BuildDocsQuality.complete,
        )
        src = _source(
            dependencies_pinned=True,
            release_artifact_present=True,
            readme_has_installation=True,
            readme_has_usage=True,
        )
        assert _replicability_github(p, src) == 10.0


# ---------------------------------------------------------------------------
# _community_github
# ---------------------------------------------------------------------------

class TestCommunity:
    def test_no_signals_returns_zero(self):
        src = _source()
        assert _community_github(src) == 0.0

    def test_has_contributing_adds_4(self):
        src = _source(has_contributing=True)
        assert _community_github(src) == 4.0

    def test_has_issue_templates_adds_3(self):
        src = _source(has_issue_templates=True)
        assert _community_github(src) == 3.0

    def test_has_code_of_conduct_adds_3(self):
        src = _source(has_code_of_conduct=True)
        assert _community_github(src) == 3.0

    def test_all_signals_returns_10(self):
        src = _source(has_contributing=True, has_issue_templates=True, has_code_of_conduct=True)
        assert _community_github(src) == 10.0


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

    def test_sil_ofl_is_open(self):
        p = _project(license="SIL-OFL-1.1")
        assert _provenance(p) == 4.0

    def test_ofl_shorthand_is_open(self):
        p = _project(license="OFL-1.1")
        assert _provenance(p) == 4.0

    def test_cc_by_is_open(self):
        p = _project(license="CC-BY-4.0")
        assert _provenance(p) == 4.0


# ---------------------------------------------------------------------------
# _is_mature
# ---------------------------------------------------------------------------

class TestIsMature:
    def _mature_source(self, days=300):
        return _source(
            release_artifact_present=True,
            last_commit=_days_ago(days),
        )

    def test_force_mature_via_field(self):
        p = _project(maturity=MaturityLevel.mature)
        assert _is_mature(p) is True

    def test_suppress_mature_via_field(self):
        p = _project(
            maturity=MaturityLevel.active,
            build_docs_quality=BuildDocsQuality.complete,
            license="MIT",
        )
        src = self._mature_source()
        assert _is_mature(p, src) is False

    def test_inferred_mature_when_all_signals_present(self):
        p = _project(build_docs_quality=BuildDocsQuality.partial, license="MIT")
        src = self._mature_source(days=300)
        assert _is_mature(p, src) is True

    def test_not_mature_without_release_artifact(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete, license="MIT")
        src = _source(last_commit=_days_ago(300))  # no release_artifact_present
        assert _is_mature(p, src) is False

    def test_not_mature_without_good_docs(self):
        p = _project(build_docs_quality=BuildDocsQuality.none, license="MIT")
        src = self._mature_source()
        assert _is_mature(p, src) is False

    def test_not_mature_without_open_license(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete, license="Proprietary")
        src = self._mature_source()
        assert _is_mature(p, src) is False

    def test_not_mature_when_too_recent(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete, license="MIT")
        src = self._mature_source(days=30)  # less than 90 days
        assert _is_mature(p, src) is False

    def test_not_mature_when_too_stale(self):
        p = _project(build_docs_quality=BuildDocsQuality.complete, license="MIT")
        src = self._mature_source(days=2000)  # more than 1825 days
        assert _is_mature(p, src) is False


# ---------------------------------------------------------------------------
# _momentum_github
# ---------------------------------------------------------------------------

class TestMomentumGithub:
    def test_no_signals_returns_floor(self):
        src = _source()
        assert _momentum_github(src) == 1.0

    def test_all_signals_returns_near_5(self):
        src = _source(
            last_commit=date.today(),
            issue_response_rate=1.0,
            release_in_last_year=True,
            has_contributing=True,
            has_issue_templates=True,
            has_code_of_conduct=True,
        )
        assert _momentum_github(src) == 5.0

    def test_score_within_bounds(self):
        src = _source(last_commit=_days_ago(60), issue_response_rate=0.5)
        m = _momentum_github(src)
        assert 1.0 <= m <= 5.0


# ---------------------------------------------------------------------------
# compute_health — now returns (availability, momentum | None, tier)
# ---------------------------------------------------------------------------

class TestComputeHealthTierBoundaries:
    """
    Tier rules (first match wins):
      archived  : activity_raw == 0.0 AND last_commit > 3 years ago
      thriving  : availability >= 4.0 AND momentum >= 4.0
      stable    : availability >= 3.0 AND momentum >= 2.5
      complete  : availability >= 3.0 AND mature AND momentum < 2.5
      dormant   : availability >= 3.0 AND NOT mature AND momentum < 2.5
      at_risk   : everything else
    """

    def test_no_source_returns_unverified(self):
        p = _project()
        availability, momentum, tier = compute_health(p)
        assert tier == HealthTier.unverified
        assert momentum is None

    def test_archived_when_activity_zero_and_commit_over_3yr(self):
        p = _project(sources=[_source(last_commit=_days_ago(1096))])
        availability, momentum, tier = compute_health(p)
        assert tier == HealthTier.archived

    def test_not_archived_when_commit_exactly_3yr(self):
        p = _project(sources=[_source(last_commit=_days_ago(1095))])
        availability, momentum, tier = compute_health(p)
        assert tier != HealthTier.archived

    def test_thriving_when_high_availability_and_momentum(self):
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
        availability, momentum, tier = compute_health(p)
        assert availability >= 4.0
        assert momentum >= 4.0
        assert tier == HealthTier.thriving

    def test_stable_when_adequate_availability_and_momentum(self):
        # availability >= 3.0 needs solid rep + AT + prov
        # rep=7 (complete+artifact+readme), at=7 (nau+end_user), prov=4 (MIT)
        # raw = 0.40*7 + 0.30*7 + 0.20*4 = 2.8+2.1+0.8 = 5.7 → avail = 3.28
        p = _project(
            build_docs_quality=BuildDocsQuality.complete,
            nothing_about_us=True,
            end_user_docs=True,
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
        availability, momentum, tier = compute_health(p)
        assert availability >= 3.0
        assert momentum >= 2.5
        assert tier == HealthTier.stable

    def test_complete_when_mature_and_low_momentum(self):
        # mature inferred: release artifact + good docs + open license + 90-1825 days old
        p = _project(
            build_docs_quality=BuildDocsQuality.complete,
            end_user_docs=True,
            license="MIT",
            sources=[_source(
                last_commit=_days_ago(400),          # old enough for maturity
                release_artifact_present=True,        # required for maturity
                readme_has_installation=True,
                readme_has_usage=True,
            )],
        )
        availability, momentum, tier = compute_health(p)
        assert availability >= 3.0
        assert tier == HealthTier.complete

    def test_dormant_when_not_mature_and_low_momentum(self):
        # Force suppress maturity, ensure availability >= 3.0 but low momentum
        # rep=7 (complete+artifact+readme), at=9 (nau+end+feedback), prov=4 (MIT)
        # raw = 0.40*7 + 0.30*9 + 0.20*4 = 2.8+2.7+0.8 = 6.3 → avail = 3.52
        p = _project(
            build_docs_quality=BuildDocsQuality.complete,
            nothing_about_us=True,
            end_user_docs=True,
            feedback_channel=True,
            license="MIT",
            maturity=MaturityLevel.active,   # suppress inferred maturity
            sources=[_source(
                last_commit=_days_ago(800),
                release_artifact_present=True,
                readme_has_installation=True,
                readme_has_usage=True,
            )],
        )
        availability, momentum, tier = compute_health(p)
        assert availability >= 3.0
        assert tier == HealthTier.dormant

    def test_at_risk_when_low_availability(self):
        p = _project(sources=[_source(last_commit=_days_ago(800))])
        availability, momentum, tier = compute_health(p)
        assert tier == HealthTier.at_risk


# ---------------------------------------------------------------------------
# compute_health — end-to-end
# ---------------------------------------------------------------------------

class TestComputeHealthEndToEnd:
    def test_returns_float_float_and_health_tier(self):
        p = _project(sources=[_source(last_commit=date.today())])
        availability, momentum, tier = compute_health(p)
        assert isinstance(availability, float)
        assert isinstance(momentum, float)
        assert isinstance(tier, HealthTier)

    def test_scores_within_bounds(self):
        p = _project(sources=[_source(
            last_commit=date.today(),
            issue_response_rate=0.5,
            release_in_last_year=True,
        )])
        availability, momentum, tier = compute_health(p)
        assert 1.0 <= availability <= 5.0
        assert 1.0 <= momentum <= 5.0

    def test_scores_rounded_to_2_decimal_places(self):
        p = _project(sources=[_source(
            last_commit=_days_ago(60),
            issue_response_rate=0.5,
        )])
        availability, momentum, tier = compute_health(p)
        assert availability == round(availability, 2)
        assert momentum == round(momentum, 2)

    def test_full_project_fixture(self):
        """Fully-populated mature project reaches availability=5.0 and momentum=5.0."""
        # Use a 300-day-old commit so _is_mature infers True (90 <= 300 <= 1825)
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
                last_commit=_days_ago(300),
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
        availability, momentum, tier = compute_health(p)
        assert availability == 5.0
        assert momentum >= 4.0  # Active tier; exact value depends on commit age
        assert tier == HealthTier.thriving
