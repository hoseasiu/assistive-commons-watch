"""Printables GraphQL API fetcher."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any, Optional

import httpx

from .base import BaseFetcher
from .models import PrintablesSource

_GRAPHQL_URL = "https://api.printables.com/graphql/"

_MODEL_ID_RE = re.compile(r"/model/(\d+)")

_QUERY = """
query PrintDetail($id: ID!) {
  print(id: $id) {
    firstPublish
    modified
    likesCount
    downloadCount
    makesCount
    remixCount
    commentCount
    dateFeatured
    userGcodeCount
    license {
      name
    }
    user {
      publicUsername
    }
  }
}
"""


def _extract_model_id(url: str) -> str:
    m = _MODEL_ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract Printables model ID from URL: {url!r}")
    return m.group(1)


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


class PrintablesFetcher(BaseFetcher):
    """Fetches public Printables model data via the GraphQL API (no auth required)."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={"Content-Type": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        )

    def fetch(self, url: str) -> PrintablesSource:
        model_id = _extract_model_id(url)

        data = self._query(model_id)
        print_data: dict[str, Any] = data.get("print") or {}

        if not print_data:
            raise ValueError(f"Printables model {model_id!r} not found or API returned no data")

        license_name: Optional[str] = (print_data.get("license") or {}).get("name")
        author: Optional[str] = (print_data.get("user") or {}).get("publicUsername")

        return PrintablesSource(
            platform="printables",
            url=url,
            fetched_at=datetime.now(timezone.utc),
            published_date=_parse_date(print_data.get("firstPublish") or print_data.get("datePublished")),
            last_updated=_parse_date(print_data.get("modified")),
            likes=print_data.get("likesCount"),
            downloads=print_data.get("downloadCount"),
            makes_count=print_data.get("makesCount"),
            remixes_count=print_data.get("remixCount"),
            comments=print_data.get("commentCount"),
            has_print_profile=(print_data.get("userGcodeCount") or 0) > 0,
            staff_pick=print_data.get("dateFeatured") is not None,
            license_cc=license_name,
            author=author,
        )

    def _query(self, model_id: str) -> dict[str, Any]:
        payload = {"query": _QUERY, "variables": {"id": model_id}}
        resp = self._client.post(_GRAPHQL_URL, json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise ValueError(f"Printables GraphQL errors: {body['errors']}")
        return body.get("data", {})

    def __enter__(self) -> PrintablesFetcher:
        return self

    def __exit__(self, *_: Any) -> None:
        self._client.close()


# Quick local test: python -m _fetchers.printables <printables-url>
if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.printables.com/model/129817-e-nable-unlimbited-phoenix-hand"
    with PrintablesFetcher() as f:
        source = f.fetch(target)
    print(json.dumps(source.model_dump(mode="json"), indent=2, default=str))
