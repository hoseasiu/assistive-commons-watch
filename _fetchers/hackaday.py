"""Hackaday.io REST API fetcher."""
from __future__ import annotations

import os
import re
from datetime import date, datetime, timezone
from typing import Any, Optional

import httpx

from .base import BaseFetcher
from .models import HackadaySource

_BASE = "https://api.hackaday.io/v1"

# Matches /project/12345 or /project/12345-some-name
_PROJECT_ID_RE = re.compile(r"hackaday\.io/project/(\d+)")


def _parse_project_id(url: str) -> str:
    m = _PROJECT_ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot parse Hackaday project ID from URL: {url!r}")
    return m.group(1)


def _to_date(ts: Optional[int | str]) -> Optional[date]:
    """Convert a Unix timestamp (int) or ISO string to a date."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).date()
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date()


class HackadayFetcher(BaseFetcher):
    """Fetches live Hackaday.io API data and returns a populated HackadaySource."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("HACKADAY_API_KEY")
        if not self._api_key:
            raise EnvironmentError(
                "HACKADAY_API_KEY env var not set. "
                "Get a free API key at https://dev.hackaday.io"
            )
        self._client = httpx.Client(timeout=30.0, follow_redirects=True)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(self, url: str) -> HackadaySource:
        project_id = _parse_project_id(url)

        project = self._get(f"/projects/{project_id}")
        logs = self._get_list(f"/projects/{project_id}/logs", sortby="created", sort_order="desc", per_page=1)
        components = self._get_list(f"/projects/{project_id}/components", per_page=1)
        files = self._get_list(f"/projects/{project_id}/files", per_page=1)
        links = self._get_list(f"/projects/{project_id}/links", per_page=50)

        # Canonical URL from API (may differ from what was stored in YAML)
        canonical_url = project.get("url") or url

        # last_log_date from the most recent log entry
        last_log_date: Optional[date] = None
        if logs:
            last_log_date = _to_date(logs[0].get("created"))

        # Total log count — re-fetch with per_page=1 to get the total from top-level
        logs_total = self._get_count(f"/projects/{project_id}/logs")

        # team_size from team_members list (the project detail returns a count field)
        team_size: Optional[int] = project.get("team_count") or project.get("team_members")
        if isinstance(team_size, list):
            team_size = len(team_size)
        if isinstance(team_size, int) and team_size < 1:
            team_size = None

        # linked GitHub URL — check the links list for github.com entries
        linked_github_url: Optional[str] = None
        for link in links:
            link_url = link.get("url", "")
            if "github.com" in link_url:
                linked_github_url = link_url
                break
        # Also check the top-level project field some older projects use
        if not linked_github_url:
            linked_github_url = project.get("github_url") or None

        return HackadaySource(
            platform="hackaday",
            url=canonical_url,
            fetched_at=datetime.now(timezone.utc),
            last_log_date=last_log_date,
            logs_count=logs_total,
            project_status=project.get("status"),
            skulls=project.get("skulls"),
            followers=project.get("followers"),
            team_size=team_size or 1,
            build_count=project.get("build_count") or project.get("builds"),
            has_components_list=bool(components),
            has_files=bool(files),
            license=project.get("license") or None,
            linked_github_url=linked_github_url,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, **params: Any) -> dict:
        resp = self._client.get(
            f"{_BASE}{path}",
            params={"api_key": self._api_key, **params},
        )
        if resp.status_code == 404:
            raise ValueError(f"Hackaday API 404: {path}")
        if resp.status_code in (401, 403, 429):
            raise PermissionError(
                f"Hackaday API auth/rate-limit error (status {resp.status_code}). "
                "Check HACKADAY_API_KEY."
            )
        resp.raise_for_status()
        return resp.json()

    def _get_list(self, path: str, **params: Any) -> list[dict]:
        """Fetch a paged Hackaday resource and return the items list."""
        data = self._get(path, **params)
        # Hackaday wraps list responses in a keyed object, e.g. {"logs": [...]}
        if isinstance(data, list):
            return data
        for val in data.values():
            if isinstance(val, list):
                return val
        return []

    def _get_count(self, path: str) -> Optional[int]:
        """Return the total item count for a paged resource (from per_page=1 response)."""
        data = self._get(path, per_page=1)
        if isinstance(data, dict):
            return data.get("total") or data.get("count") or None
        return None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> HackadayFetcher:
        return self

    def __exit__(self, *_: Any) -> None:
        self._client.close()


# Quick local test: python -m _fetchers.hackaday <hackaday-url>
if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://hackaday.io/project/175211"
    with HackadayFetcher() as f:
        source = f.fetch(target)
    print(json.dumps(source.model_dump(mode="json"), indent=2, default=str))
