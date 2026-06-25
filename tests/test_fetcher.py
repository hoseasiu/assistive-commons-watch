"""Tests for _fetchers/github.py — URL parsing, mocked HTTP, README regexes."""
from __future__ import annotations

import base64
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from _fetchers.github import (
    GitHubFetcher,
    _RE_BOM,
    _RE_INSTALL,
    _RE_USAGE,
    _parse_owner_repo,
)
from _fetchers.models import GitHubSource


# ---------------------------------------------------------------------------
# _parse_owner_repo
# ---------------------------------------------------------------------------

class TestParseOwnerRepo:
    def test_simple_url(self):
        owner, repo = _parse_owner_repo("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_url_with_trailing_slash(self):
        owner, repo = _parse_owner_repo("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    def test_url_with_dot_git_suffix(self):
        owner, repo = _parse_owner_repo("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    def test_org_with_hyphens(self):
        owner, repo = _parse_owner_repo("https://github.com/my-org/my-repo")
        assert owner == "my-org"
        assert repo == "my-repo"

    def test_invalid_url_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot parse GitHub owner/repo"):
            _parse_owner_repo("https://gitlab.com/owner/repo")

    def test_non_url_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot parse GitHub owner/repo"):
            _parse_owner_repo("not-a-url")

    def test_github_url_missing_repo_raises(self):
        with pytest.raises(ValueError, match="Cannot parse GitHub owner/repo"):
            _parse_owner_repo("https://github.com/owner")

    def test_github_root_raises(self):
        with pytest.raises(ValueError, match="Cannot parse GitHub owner/repo"):
            _parse_owner_repo("https://github.com/")


# ---------------------------------------------------------------------------
# README section detection regexes
# ---------------------------------------------------------------------------

class TestReadmeRegexes:
    # _RE_INSTALL
    def test_install_matches_installation_heading(self):
        assert _RE_INSTALL.search("## Installation")

    def test_install_matches_getting_started(self):
        assert _RE_INSTALL.search("## Getting Started")

    def test_install_matches_quickstart(self):
        assert _RE_INSTALL.search("## Quick Start")

    def test_install_matches_h3(self):
        assert _RE_INSTALL.search("### Installation Guide")

    def test_install_no_match_on_plain_text(self):
        assert not _RE_INSTALL.search("This project has no special setup required.")

    def test_install_case_insensitive(self):
        assert _RE_INSTALL.search("## INSTALLATION")

    # _RE_USAGE
    def test_usage_matches_usage_heading(self):
        assert _RE_USAGE.search("## Usage")

    def test_usage_matches_how_to_use(self):
        assert _RE_USAGE.search("## How to Use")

    def test_usage_matches_examples(self):
        assert _RE_USAGE.search("## Examples")

    def test_usage_matches_demo(self):
        assert _RE_USAGE.search("## Demo")

    def test_usage_no_match_plain_text(self):
        assert not _RE_USAGE.search("Here is some random content.")

    def test_usage_case_insensitive(self):
        assert _RE_USAGE.search("## USAGE")

    # _RE_BOM
    def test_bom_matches_bill_of_materials(self):
        assert _RE_BOM.search("## Bill of Materials")

    def test_bom_matches_bom_heading(self):
        assert _RE_BOM.search("## BOM")

    def test_bom_matches_materials(self):
        assert _RE_BOM.search("## Materials")

    def test_bom_matches_components(self):
        assert _RE_BOM.search("## Components")

    def test_bom_matches_parts_list(self):
        assert _RE_BOM.search("## Parts List")

    def test_bom_no_match_plain_text(self):
        assert not _RE_BOM.search("This is a software-only project.")

    def test_bom_case_insensitive(self):
        assert _RE_BOM.search("## BILL OF MATERIALS")

    def test_bom_h3_heading(self):
        assert _RE_BOM.search("### Components Required")

    # Multiline README content
    def test_install_in_multiline_readme(self):
        readme = "# My Project\n\nSome intro.\n\n## Installation\n\nRun `pip install`."
        assert _RE_INSTALL.search(readme)

    def test_bom_in_multiline_readme(self):
        readme = "# Hardware Project\n\n## Overview\n\nCool stuff.\n\n## Bill of Materials\n\n- Wire\n- Resistor"
        assert _RE_BOM.search(readme)

    def test_no_headings_no_match(self):
        readme = "This project uses installation and usage patterns but has no headings."
        assert not _RE_INSTALL.search(readme)


# ---------------------------------------------------------------------------
# GitHubFetcher.fetch — mocked HTTP calls
# ---------------------------------------------------------------------------

def _make_mock_response(json_data, status_code=200):
    """Build a mock httpx Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    resp.headers = {}
    return resp


def _make_fetcher_with_mocked_client(mock_get_side_effect, mock_head_status=200):
    """
    Create a GitHubFetcher whose internal httpx.Client._get is fully mocked.
    We patch httpx.Client.__init__ to avoid real HTTP connections.
    """
    fetcher = GitHubFetcher.__new__(GitHubFetcher)
    fetcher._client = MagicMock()
    fetcher._client.get.side_effect = mock_get_side_effect
    return fetcher


class TestGitHubFetcherMocked:
    """Test GitHubFetcher.fetch() using mocked httpx responses."""

    def _build_mock_responses(
        self,
        *,
        stars=42,
        forks=5,
        last_commit_iso="2024-06-01T12:00:00Z",
        open_issues=3,
        html_url="https://github.com/owner/repo",
        has_contributing=True,
        has_code_of_conduct=True,
        has_issue_template=True,
        readme_content="## Installation\n\nInstall it.\n\n## Usage\n\nUse it.",
        releases=None,
        issues=None,
        issue_comments=None,
        commits=None,
    ):
        """Return a dict mapping URL paths to their mock responses.

        issue_comments: dict mapping issue number → list of comment dicts.
        Used to populate per-issue comment endpoints so _response_rate can check
        whether any comment is from a non-author.
        """
        if releases is None:
            releases = [{"draft": False, "published_at": "2024-06-01T00:00:00Z", "assets": [{"name": "bin"}]}]
        if issues is None:
            issues = [{"number": 1, "user": {"login": "reporter"}, "comments": 1}]
        if issue_comments is None:
            issue_comments = {1: [{"user": {"login": "maintainer"}}]}
        if commits is None:
            commits = [{"commit": {"committer": {"date": last_commit_iso}}}]

        encoded_readme = base64.b64encode(readme_content.encode()).decode()

        responses = {
            "/repos/owner/repo": {
                "stargazers_count": stars,
                "forks_count": forks,
                "open_issues_count": open_issues,
                "html_url": html_url,
            },
            "/repos/owner/repo/community/profile": {
                "files": {
                    "contributing": {"url": "x"} if has_contributing else None,
                    "code_of_conduct": {"url": "x"} if has_code_of_conduct else None,
                    "issue_template": {"url": "x"} if has_issue_template else None,
                }
            },
            "/repos/owner/repo/readme": {
                "content": encoded_readme,
                "encoding": "base64",
            },
            "/repos/owner/repo/releases?per_page=5": releases,
            "/repos/owner/repo/issues?state=all&per_page=20": issues,
            "/repos/owner/repo/commits?per_page=1": commits,
        }
        for issue_num, comments in issue_comments.items():
            responses[f"/repos/owner/repo/issues/{issue_num}/comments?per_page=5"] = comments
        return responses

    def _make_fetcher(self, responses: dict) -> GitHubFetcher:
        fetcher = GitHubFetcher.__new__(GitHubFetcher)

        def mock_get(url: str):
            # Strip the base URL prefix
            base = "https://api.github.com"
            path = url[len(base):]
            data = responses.get(path)
            if data is None:
                # Simulate 404 for unknown paths (e.g. ISSUE_TEMPLATE directory check)
                resp = _make_mock_response({}, status_code=200)
                resp.status_code = 404
                return resp
            return _make_mock_response(data)

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        fetcher._client = mock_client
        return fetcher

    def test_fetch_returns_github_source(self):
        responses = self._build_mock_responses()
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert isinstance(result, GitHubSource)

    def test_fetch_populates_stars_and_forks(self):
        responses = self._build_mock_responses(stars=100, forks=20)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.stars == 100
        assert result.forks == 20

    def test_fetch_populates_last_commit(self):
        responses = self._build_mock_responses(last_commit_iso="2024-03-15T10:00:00Z")
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.last_commit == date(2024, 3, 15)

    def test_fetch_readme_install_detected(self):
        readme = "## Installation\n\nRun pip install."
        responses = self._build_mock_responses(readme_content=readme)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.readme_has_installation is True

    def test_fetch_readme_usage_detected(self):
        readme = "## Usage\n\nRun the binary."
        responses = self._build_mock_responses(readme_content=readme)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.readme_has_usage is True

    def test_fetch_readme_bom_detected(self):
        readme = "## Bill of Materials\n\n- Wire\n- Resistor"
        responses = self._build_mock_responses(readme_content=readme)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.readme_has_bom is True

    def test_fetch_readme_no_bom(self):
        readme = "## Installation\n\nInstall it.\n\n## Usage\n\nUse it."
        responses = self._build_mock_responses(readme_content=readme)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.readme_has_bom is False

    def test_fetch_community_contributing(self):
        responses = self._build_mock_responses(has_contributing=True)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.has_contributing is True

    def test_fetch_community_no_contributing(self):
        responses = self._build_mock_responses(has_contributing=False)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.has_contributing is False

    def test_fetch_release_in_last_year_true(self):
        today_iso = date.today().isoformat() + "T00:00:00Z"
        releases = [{"draft": False, "published_at": today_iso, "assets": []}]
        responses = self._build_mock_responses(releases=releases)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.release_in_last_year is True

    def test_fetch_issue_response_rate(self):
        issues = [
            {"number": 1, "user": {"login": "alice"}, "comments": 2},   # maintainer commented
            {"number": 2, "user": {"login": "alice"}, "comments": 0},   # no comments
            {"number": 3, "user": {"login": "bob"}, "comments": 1},     # maintainer commented
            {"number": 4, "user": {"login": "carol"}, "comments": 0},   # no comments
        ]
        issue_comments = {
            1: [{"user": {"login": "maintainer"}}, {"user": {"login": "alice"}}],
            3: [{"user": {"login": "maintainer"}}],
        }
        responses = self._build_mock_responses(issues=issues, issue_comments=issue_comments)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        # 2 out of 4 responded -> 0.5
        assert result.issue_response_rate == pytest.approx(0.5)

    def test_fetch_issue_response_rate_filters_self_comments(self):
        """An issue where only the reporter commented must not count as responded."""
        issues = [{"number": 1, "user": {"login": "reporter"}, "comments": 2}]
        issue_comments = {1: [{"user": {"login": "reporter"}}, {"user": {"login": "reporter"}}]}
        responses = self._build_mock_responses(issues=issues, issue_comments=issue_comments)
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.issue_response_rate == pytest.approx(0.0)

    def test_fetch_prs_excluded_from_response_rate(self):
        issues = [
            {"number": 1, "user": {"login": "reporter"}, "comments": 0},
            {"number": 2, "pull_request": {"url": "x"}, "user": {"login": "reporter"}, "comments": 5},  # PR — excluded
        ]
        responses = self._build_mock_responses(issues=issues, issue_comments={})
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        # Only issue 1 counts: 0/1 responded = 0.0
        assert result.issue_response_rate == pytest.approx(0.0)

    def test_fetch_platform_is_github(self):
        responses = self._build_mock_responses()
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.platform == "github"

    def test_fetch_sets_fetched_at(self):
        responses = self._build_mock_responses()
        fetcher = self._make_fetcher(responses)
        result = fetcher.fetch("https://github.com/owner/repo")
        assert result.fetched_at is not None
        assert isinstance(result.fetched_at, datetime)

    def test_fetch_404_raises_value_error(self):
        fetcher = GitHubFetcher.__new__(GitHubFetcher)
        mock_client = MagicMock()
        mock_client.get.return_value = _make_mock_response({}, status_code=404)
        fetcher._client = mock_client
        with pytest.raises(ValueError, match="GitHub API 404"):
            fetcher.fetch("https://github.com/owner/repo")

    def test_fetch_rate_limit_raises_permission_error(self):
        fetcher = GitHubFetcher.__new__(GitHubFetcher)
        resp = _make_mock_response({}, status_code=403)
        resp.headers = {"X-RateLimit-Reset": "9999999999"}
        mock_client = MagicMock()
        mock_client.get.return_value = resp
        fetcher._client = mock_client
        with pytest.raises(PermissionError, match="rate limit"):
            fetcher.fetch("https://github.com/owner/repo")
