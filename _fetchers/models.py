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


class MaturityLevel(str, Enum):
    active = "active"   # suppress inferred maturity bonus
    mature = "mature"   # force-apply maturity bonus


class HealthTier(str, Enum):
    thriving = "thriving"
    stable = "stable"
    complete = "complete"
    dormant = "dormant"
    at_risk = "at_risk"
    archived = "archived"
    unverified = "unverified"
    documented = "documented"  # static-platform-only projects; UI shows build-readiness, not health


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


class InstructablesSource(BaseModel):
    platform: Literal["instructables"]
    url: str
    fetched_at: Optional[datetime] = None

    published_date: Optional[date] = None
    views: Optional[int] = Field(None, ge=0)
    favorites: Optional[int] = Field(None, ge=0)
    imadeit_count: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)

    step_count: Optional[int] = Field(None, ge=0)
    has_bom_step: Optional[bool] = None
    has_download_files: Optional[bool] = None
    contest_winner: Optional[bool] = None

    license_cc: Optional[str] = None
    author: Optional[str] = None


class PrintablesSource(BaseModel):
    platform: Literal["printables"]
    url: str
    fetched_at: Optional[datetime] = None

    published_date: Optional[date] = None
    last_updated: Optional[date] = None
    likes: Optional[int] = Field(None, ge=0)
    downloads: Optional[int] = Field(None, ge=0)
    makes_count: Optional[int] = Field(None, ge=0)
    remixes_count: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)

    has_print_profile: Optional[bool] = None
    staff_pick: Optional[bool] = None

    license_cc: Optional[str] = None
    author: Optional[str] = None


class ThingiverseSource(BaseModel):
    platform: Literal["thingiverse"]
    url: str
    fetched_at: Optional[datetime] = None

    published_date: Optional[date] = None
    last_updated: Optional[date] = None
    likes: Optional[int] = Field(None, ge=0)
    downloads: Optional[int] = Field(None, ge=0)
    makes_count: Optional[int] = Field(None, ge=0)
    remixes_count: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)

    featured: Optional[bool] = None

    license_cc: Optional[str] = None
    author: Optional[str] = None


class MyMiniFactorySource(BaseModel):
    platform: Literal["myminifactory"]
    url: str
    fetched_at: Optional[datetime] = None

    published_date: Optional[date] = None
    likes: Optional[int] = Field(None, ge=0)
    makes_count: Optional[int] = Field(None, ge=0)
    comments: Optional[int] = Field(None, ge=0)

    is_free: Optional[bool] = None
    guaranteed_printable: Optional[bool] = None
    in_enable_category: Optional[bool] = None

    license_cc: Optional[str] = None
    author: Optional[str] = None


class HackadaySource(BaseModel):
    platform: Literal["hackaday"]
    url: str
    fetched_at: Optional[datetime] = None

    last_log_date: Optional[date] = None
    logs_count: Optional[int] = Field(None, ge=0)
    project_status: Optional[str] = None

    skulls: Optional[int] = Field(None, ge=0)
    followers: Optional[int] = Field(None, ge=0)
    team_size: Optional[int] = Field(None, ge=1)
    build_count: Optional[int] = Field(None, ge=0)

    has_components_list: Optional[bool] = None
    has_files: Optional[bool] = None

    license: Optional[str] = None
    linked_github_url: Optional[str] = None


# Discriminated union over all source platforms.
# Pydantic uses the `platform` literal to select the right model at parse time.
Source = Annotated[
    Union[
        GitHubSource,
        InstructablesSource,
        PrintablesSource,
        ThingiverseSource,
        MyMiniFactorySource,
        HackadaySource,
    ],
    Field(discriminator="platform"),
]


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

    # Maturity — curator override for the maturity bonus (None = infer)
    maturity: Optional[MaturityLevel] = None

    # Computed — written back by fetch workflow, not hand-edited
    health_tier: Optional[HealthTier] = None
    health_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    availability_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    momentum_score: Optional[float] = Field(None, ge=1.0, le=5.0)
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
