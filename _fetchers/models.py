from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class Modality(str, Enum):
    hardware = "hardware"
    software = "software"
    firmware = "firmware"
    hybrid = "hybrid"


class SkillLevel(str, Enum):
    beginner = "beginner"
    maker = "maker"
    engineer = "engineer"


class BuildDocsQuality(str, Enum):
    none = "none"
    partial = "partial"
    complete = "complete"


class HealthTier(str, Enum):
    thriving = "thriving"
    stable = "stable"
    dormant = "dormant"
    at_risk = "at_risk"
    archived = "archived"
    unverified = "unverified"


class AtRelevance(str, Enum):
    primary = "primary"    # directly increases functional capability (NVDA, OptiKey, LipSync)
    adjacent = "adjacent"  # AT-enabling infrastructure (liblouis, etc.)
    tooling = "tooling"    # developer/auditing tool with AT application


class GitHubSource(BaseModel):
    platform: Literal["github"]
    url: str
    fetched_at: Optional[datetime] = None
    latest_release_url: Optional[str] = None

    # Activity signals
    stars: Optional[int] = Field(None, ge=0)
    forks: Optional[int] = Field(None, ge=0)
    last_commit: Optional[date] = None
    open_issues: Optional[int] = Field(None, ge=0)
    open_prs: Optional[int] = Field(None, ge=0)
    issue_response_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    release_in_last_year: Optional[bool] = None

    # Replicability signals
    readme_has_installation: Optional[bool] = None
    readme_has_usage: Optional[bool] = None
    readme_has_bom: Optional[bool] = None
    release_artifact_present: Optional[bool] = None
    dependencies_pinned: Optional[bool] = None

    # Community health signals
    has_contributing: Optional[bool] = None
    has_code_of_conduct: Optional[bool] = None
    has_issue_templates: Optional[bool] = None

    # Provenance signals (auto-populated by fetcher)
    license_spdx: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        if not v.startswith("https://github.com/"):
            raise ValueError("GitHub source URL must start with https://github.com/")
        return v


# Discriminated union over all source platforms — add new source types here when Phase 2 lands.
# Pydantic uses the `platform` literal to select the right model at parse time.
Source = Annotated[Union[GitHubSource], Field(discriminator="platform")]


class Project(BaseModel):
    # Identity
    id: str
    name: str
    description: str
    at_relevance: AtRelevance = AtRelevance.primary
    added_date: date
    tags: list[str] = []

    # Scope
    disability_area: list[str] = []
    iso_9999_codes: list[str] | None = None
    modality: Modality
    user_context: list[str] = []
    interface: list[str] = []
    platform: list[str] = []
    plain_language_description: Optional[str] = None

    # Replicability (manually curated)
    bom_present: Optional[bool] = None
    build_docs_quality: BuildDocsQuality = BuildDocsQuality.none
    cost_range: Optional[str] = None
    fabrication_methods: list[str] = []
    skill_level: Optional[SkillLevel] = None

    # AT-specific (manually curated)
    nothing_about_us: Optional[bool] = None
    replicated_by_disabled_person: Optional[bool] = None
    end_user_docs: Optional[bool] = None
    feedback_channel: Optional[bool] = None
    known_deployed_instances: Optional[str] = None

    # Provenance (manually curated)
    license: Optional[str] = None
    associated_publication: Optional[str] = None
    institutional_affiliation: Optional[str] = None
    origin_program: Optional[str] = None

    # Documentation
    documentation_languages: list[str] = ["en"]

    # Ecosystem cross-references (manually curated)
    # Keys are registry slugs (makers_making_change, openassistive, goat, eastin, awesome_assistivetech).
    # Values are full URLs to the project's page in that registry.
    ecosystem_links: Optional[dict[str, str]] = None

    # Sources — populated by fetch workflow
    sources: list[Source] = []

    # Computed — written back by fetch workflow, not hand-edited
    health_tier: Optional[HealthTier] = None
    health_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    scored_with: Optional[str] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.fullmatch(r"acw-\d{4}", v):
            raise ValueError("id must match acw-NNNN (e.g. acw-0001)")
        return v

    @field_validator("documentation_languages")
    @classmethod
    def languages_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("documentation_languages must not be empty")
        return v
