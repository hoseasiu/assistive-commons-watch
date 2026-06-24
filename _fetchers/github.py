"""GitHub REST API fetcher (Phase 1)."""
from __future__ import annotations

import base64
import os
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from .base import BaseFetcher
from .models import GitHubSource

_OWNER_REPO_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git|/)?$")

# README section detection — matches ATX headings (# / ## / ###)
_RE_INSTALL = re.compile(r"^#{1,3}\s+.*(install|getting\s+started|quick\s*start)", re.I | re.M)
_RE_USAGE = re.compile(r"^#{1,3}\s+.*(usage|how\s+to\s+use|quickstart|examples?|demo)", re.I | re.M)
_RE_BOM = re.compile(
    r"^#{1,3}\s+.*(bill\s+of\s+materials?|bom|materials?|components?|parts?\s+list)",
    re.I | re.M,
)


def _parse_owner_repo(url: str) -> tuple[str, str]:
    m = _OWNER_REPO_RE.match(url.rstrip("/"))
    if not m:
        raise ValueError(f"Cannot parse GitHub owner/repo from URL: {url!r}")
    return m.group(1), m.group(2)


def _to_date(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()


class GitHubFetcher(BaseFetcher):
    """Fetches live GitHub API data and returns a populated GitHubSource."""

    _BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None) -> None:
        tok = token or os.environ.get("GITHUB_TOKEN")
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        self._client = httpx.Client(headers=headers, timeout=30.0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(self, url: str) -> GitHubSource:
        owner, repo = _parse_owner_repo(url)

        meta = self._get(f"/repos/{owner}/{repo}")
        community = self._get(f"/repos/{owner}/{repo}/community/profile")
        readme = self._fetch_readme(owner, repo)
        releases = self._get(f"/repos/{owner}/{repo}/releases?per_page=5")
        issues = self._get(f"/repos/{owner}/{repo}/issues?state=all&per_page=20")
        commits = self._get(f"/repos/{owner}/{repo}/commits?per_page=1")
        has_tmpl_dir = self._path_exists(owner, repo, ".github/ISSUE_TEMPLATE")

        published = [r for r in releases if not r.get("draft", False)]
        one_year_ago = date.today() - timedelta(days=365)

        return GitHubSource(
            platform="github",
            url=url,
            fetched_at=datetime.now(timezone.utc),
            # Activity
            stars=meta.get("stargazers_count"),
            forks=meta.get("forks_count"),
            # open_issues_count includes PRs — acceptable approximation
            open_issues=meta.get("open_issues_count"),
            last_commit=self._last_commit_date(commits),
            issue_response_rate=self._response_rate(issues),
            release_in_last_year=any(
                _to_date(r.get("published_at")) >= one_year_ago
                for r in published
                if _to_date(r.get("published_at"))
            ) or False,
            # Replicability
            readme_has_installation=bool(_RE_INSTALL.search(readme)) if readme else None,
            readme_has_usage=bool(_RE_USAGE.search(readme)) if readme else None,
            readme_has_bom=bool(_RE_BOM.search(readme)) if readme else None,
            release_artifact_present=any(r.get("assets") for r in published) or False,
            # dependencies_pinned: not yet implemented — requires per-language heuristics
            # Community health
            has_contributing=self._file_present(community, "contributing"),
            has_code_of_conduct=self._file_present(community, "code_of_conduct"),
            # Community profile misses .github/ISSUE_TEMPLATE/ directories — check both
            has_issue_templates=(
                self._file_present(community, "issue_template") or has_tmpl_dir
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get(self, path: str) -> Any:
        resp = self._client.get(f"{self._BASE}{path}")
        if resp.status_code == 404:
            raise ValueError(f"GitHub API 404: {path}")
        if resp.status_code in (403, 429):
            reset = resp.headers.get("X-RateLimit-Reset", "unknown")
            raise PermissionError(
                f"GitHub API rate limit or auth error (status {resp.status_code}). "
                f"Rate limit resets at: {reset}. Set GITHUB_TOKEN to raise the limit."
            )
        resp.raise_for_status()
        return resp.json()

    def _fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        try:
            data = self._get(f"/repos/{owner}/{repo}/readme")
        except ValueError:
            return None
        raw = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(raw).decode("utf-8", errors="replace")
        return raw

    def _path_exists(self, owner: str, repo: str, path: str) -> bool:
        resp = self._client.get(
            f"{self._BASE}/repos/{owner}/{repo}/contents/{path}"
        )
        return resp.status_code == 200

    def _last_commit_date(self, commits: list[dict]) -> Optional[date]:
        if not commits:
            return None
        return _to_date(
            commits[0].get("commit", {}).get("committer", {}).get("date")
        )

    def _response_rate(self, items: list[dict]) -> Optional[float]:
        # The issues endpoint returns both issues and PRs; filter PRs out
        issues = [i for i in items if "pull_request" not in i]
        if not issues:
            return None
        responded = sum(1 for i in issues if i.get("comments", 0) > 0)
        return round(responded / len(issues), 2)

    @staticmethod
    def _file_present(community: dict, key: str) -> bool:
        return community.get("files", {}).get(key) is not None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> GitHubFetcher:
        return self

    def __exit__(self, *_: Any) -> None:
        self._client.close()


# Quick local test: python -m _fetchers.github <github-url>
if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/OptiKey/OptiKey"
    with GitHubFetcher() as f:
        source = f.fetch(target)
    print(json.dumps(source.model_dump(mode="json"), indent=2, default=str))
