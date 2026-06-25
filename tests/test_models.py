"""Tests for _fetchers/models.py — Pydantic model validators."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from _fetchers.models import GitHubSource, Project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_project(**overrides) -> dict:
    """Return the minimum fields needed to construct a valid Project."""
    base = {
        "id": "acw-0001",
        "name": "Test Project",
        "description": "A test project",
        "added_date": "2024-01-01",
        "modality": "software",
    }
    base.update(overrides)
    return base


def _minimal_github_source(**overrides) -> dict:
    """Return the minimum fields needed to construct a valid GitHubSource."""
    base = {
        "platform": "github",
        "url": "https://github.com/owner/repo",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Project.id validator
# ---------------------------------------------------------------------------

class TestProjectIdValidator:
    def test_valid_id_passes(self):
        p = Project(**_minimal_project(id="acw-0001"))
        assert p.id == "acw-0001"

    def test_valid_id_large_number_passes(self):
        p = Project(**_minimal_project(id="acw-9999"))
        assert p.id == "acw-9999"

    def test_too_few_digits_fails(self):
        with pytest.raises(ValidationError, match="acw-NNNN"):
            Project(**_minimal_project(id="acw-1"))

    def test_three_digits_fails(self):
        with pytest.raises(ValidationError, match="acw-NNNN"):
            Project(**_minimal_project(id="acw-001"))

    def test_no_prefix_fails(self):
        with pytest.raises(ValidationError, match="acw-NNNN"):
            Project(**_minimal_project(id="foo"))

    def test_wrong_prefix_fails(self):
        with pytest.raises(ValidationError, match="acw-NNNN"):
            Project(**_minimal_project(id="proj-0001"))

    def test_extra_digits_fails(self):
        with pytest.raises(ValidationError, match="acw-NNNN"):
            Project(**_minimal_project(id="acw-00001"))


# ---------------------------------------------------------------------------
# Project.documentation_languages validator
# ---------------------------------------------------------------------------

class TestDocumentationLanguagesValidator:
    def test_default_is_en(self):
        p = Project(**_minimal_project())
        assert p.documentation_languages == ["en"]

    def test_single_language_passes(self):
        p = Project(**_minimal_project(documentation_languages=["fr"]))
        assert p.documentation_languages == ["fr"]

    def test_multiple_languages_passes(self):
        p = Project(**_minimal_project(documentation_languages=["en", "es", "fr"]))
        assert p.documentation_languages == ["en", "es", "fr"]

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError, match="documentation_languages must not be empty"):
            Project(**_minimal_project(documentation_languages=[]))


# ---------------------------------------------------------------------------
# GitHubSource URL validator
# ---------------------------------------------------------------------------

class TestGitHubSourceUrlValidator:
    def test_valid_github_url_passes(self):
        src = GitHubSource(**_minimal_github_source())
        assert src.url == "https://github.com/owner/repo"

    def test_valid_github_url_with_org_passes(self):
        src = GitHubSource(**_minimal_github_source(url="https://github.com/my-org/my-repo"))
        assert src.url == "https://github.com/my-org/my-repo"

    def test_non_github_url_fails(self):
        with pytest.raises(ValidationError, match="must start with https://github.com/"):
            GitHubSource(**_minimal_github_source(url="https://gitlab.com/owner/repo"))

    def test_http_not_https_fails(self):
        with pytest.raises(ValidationError, match="must start with https://github.com/"):
            GitHubSource(**_minimal_github_source(url="http://github.com/owner/repo"))

    def test_random_url_fails(self):
        with pytest.raises(ValidationError, match="must start with https://github.com/"):
            GitHubSource(**_minimal_github_source(url="https://example.com/owner/repo"))


# ---------------------------------------------------------------------------
# GitHubSource.issue_response_rate constraint (ge=0.0, le=1.0)
# ---------------------------------------------------------------------------

class TestIssueResponseRateConstraint:
    def test_zero_passes(self):
        src = GitHubSource(**_minimal_github_source(issue_response_rate=0.0))
        assert src.issue_response_rate == 0.0

    def test_one_passes(self):
        src = GitHubSource(**_minimal_github_source(issue_response_rate=1.0))
        assert src.issue_response_rate == 1.0

    def test_mid_value_passes(self):
        src = GitHubSource(**_minimal_github_source(issue_response_rate=0.75))
        assert src.issue_response_rate == 0.75

    def test_none_passes(self):
        src = GitHubSource(**_minimal_github_source(issue_response_rate=None))
        assert src.issue_response_rate is None

    def test_below_zero_raises(self):
        with pytest.raises(ValidationError):
            GitHubSource(**_minimal_github_source(issue_response_rate=-0.1))

    def test_above_one_raises(self):
        with pytest.raises(ValidationError):
            GitHubSource(**_minimal_github_source(issue_response_rate=1.1))
