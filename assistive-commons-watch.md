# Assistive Commons Watch — Project Brief

## Concept

**Assistive Commons Watch (ACW)** is a living registry and health-monitoring dashboard for open-source assistive technology projects. It is scoped initially to GitHub-hosted projects, with a data model designed to extend to other platforms (Printables, Thingiverse, Instructables, Hackaday.io, Zenodo, OSF, EASTIN, GARI) in future phases.

ACW is explicitly **more than an awesome list**. Where an awesome list is a curated link dump with brief descriptions, ACW is a queryable, filterable registry that reflects the actual health and usability of projects over time — a live dashboard of the open AT space.

### Name rationale
- **Assistive** — scoped to tools that increase functional capability for people with disabilities
- **Commons** — signals community ownership and stewardship; the data is openly licensed (CC0), the scoring methodology is transparent and versioned, and attribution flows back to projects and contributors
- **Watch** — signals the living/monitoring angle; when someone lands on the site they should feel like they're viewing a live dashboard, not browsing a directory

### Scope statement
ACW tracks open-source assistive technology projects — tools designed to increase functional capability for people with disabilities, where the design, code, or fabrication files are publicly available for replication or modification. This scopes out commercial tools, pure advocacy projects, and general accessibility libraries, while keeping the focus on replicable/buildable things.

---

## What ACW Tracks

### Project identity & scope
- Name, description, source URL(s), homepage/demo
- Target disability/access need (categorical + freetext)
- Modality: hardware / software / firmware / hybrid
- Intended user context: daily living, communication, mobility, education, workplace, recreation
- Input/output interface: sEMG, eye gaze, switch, voice, etc.

### Maintenance & activity signals
- Maintenance status: Active / Passive / Archived / Abandoned / Seeking Maintainer
- Last commit date, open issue count, open PRs (auto-fetched)
- Issue response rate (% of recent issues that received a response)
- Explicitly stated license
- CONTRIBUTING.md and CODE_OF_CONDUCT present (community health signals)

### Replicability *(critical for AT)*
- Bill of Materials (BOM) available: Y/N
- Assembly/build instructions quality: None / Partial / Complete
- Estimated build cost range
- Required fabrication methods: 3D print, PCB, off-shelf only, etc.
- Dependencies listed and pinned vs. floating
- Packaged release artifact available (binary, STL, gerbers) vs. source-only

### Co-design & disability community involvement
- "Nothing About Us Without Us" (NAUWU) indicator: was the project built with or by disabled people?
- Co-designer/user tester credited?
- Feedback/contact channel available for end users
- End-user documentation present (vs. developer docs only)

### Usability & distribution
- Available as a finished product anywhere (Printables, Instructables, etc.)?
- Documentation language(s)
- Skill level required to replicate: Beginner / Maker / Engineer
- Accessibility of the documentation itself

### Research & provenance
- Associated publication or citation
- Academic or institutional affiliation
- Originating program or challenge (e.g., CRE[AT]E, RESNA, ATHack)

### Community signals (auto-fetched)
- GitHub stars, forks
- Linked in any standards body or registry (GARI, EASTIN)?
- Known deployed instances ("X people are using this")

---

## Data Model

Each project is a single YAML file. Fields are split into **platform-agnostic** (canonical record) and **platform-specific** (one block per source). This is the key architectural decision that enables future platform expansion.

```yaml
# Canonical record — platform-agnostic
id: "acw-0042"
name: "HeadMouse Nano"
description: "..."
added_date: "2025-01-15"
tags: [eye-gaze, mouse-emulation, hardware]
disability_area: [motor, mobility]
modality: hardware
user_context: [daily-living, workplace]
interface: [head-tracking]
nothing_about_us: true
replicated_by_disabled_person: false
build_docs_quality: complete   # none | partial | complete
cost_range: "$50–$150"
fabrication_methods: [3d-print, off-shelf]
skill_level: maker             # beginner | maker | engineer
license: MIT
associated_publication: "https://..."
origin_program: null
documentation_languages: [en]

# Platform-specific blocks — one entry per source platform
sources:
  - platform: github
    url: "https://github.com/org/repo"
    fetched_at: "2026-06-23T04:00:00Z"
    stars: 312
    forks: 47
    last_commit: "2026-05-10"
    open_issues: 8
    has_contributing: true
    has_code_of_conduct: false
    maintenance_status: active   # auto-derived
  - platform: printables          # future
    url: "https://printables.com/model/..."
    fetched_at: "2026-06-23T04:00:00Z"
    downloads: 1840
    makes: 23
```

---

## Health Score System

### Design principles
- **Don't penalize small/solo projects** for lacking a CODE_OF_CONDUCT — these metrics were designed for large OSS, not single-person AT tools built for a specific user
- **Don't let stars/forks dominate** — AT projects serve small populations by definition; popularity is a misleading proxy for quality
- **Make the score explainable** — every dimension is shown in plain language on the project detail page
- **Log score changes** — when a project's tier changes, the event is recorded and visible (e.g., "HeadMouse Nano moved from Stable to Dormant — last commit was 14 months ago")

### Score dimensions

**1. Activity** — is anyone home?
- Days since last commit (decay curve, not cliff)
- Issue response rate: % of last N issues that received a response
- PR merge rate / average time to close
- Release cadence (tagged releases signal intentional maintenance)

**2. Replicability** — can someone actually build this?
- README quality (section detection: Installation? Usage? BOM?)
- Build docs presence and completeness
- Dependencies pinned vs. floating
- Release artifact present (binary, STL, gerbers) vs. source-only

**3. Community health** — is it welcoming?
- CONTRIBUTING.md present
- Issue templates present
- Code of conduct present

**4. AT-specific signals** — the layer no generic tool has
- NAUWU / co-design indicator (manually curated)
- End-user documentation present
- Accessibility of documentation
- Known deployed instances

**5. Provenance & trust**
- OSI-approved license present
- Associated publication or citation
- Affiliated with a known program or institution

### Tier system (headline display)

| Tier | Label | Meaning |
|---|---|---|
| 🟢 | Thriving | Active, documented, welcoming |
| 🔵 | Stable | Works, maintained passively, usable |
| 🟡 | Dormant | Not recently active, but documented enough to replicate |
| 🟠 | At Risk | Useful but maintenance unclear, documentation gaps |
| 🔴 | Archived | Explicitly archived or clearly abandoned |
| ⚪ | Unverified | Newly submitted, not yet assessed |

### Detail view
Each project's detail page shows a **radar/spider chart** across the five dimensions above, so users can see *why* a project has its tier — not just what the tier is.

---

## Repository & Site Architecture

```
assistive-commons-watch/
├── _data/
│   └── projects/              # one YAML file per project
│       ├── headmouse-nano.yaml
│       └── ...
├── _fetchers/
│   ├── base.py                # abstract Fetcher class
│   ├── github.py              # GitHub API fetcher (Phase 1)
│   └── (printables.py)        # future phases
├── .github/
│   └── workflows/
│       ├── fetch.yml          # nightly: fetch all sources, commit diffs
│       └── validate.yml       # on PR: validate YAML schema
├── scripts/
│   └── add_project.py         # CLI to scaffold a new project entry
└── site/                      # 11ty frontend
    ├── index.njk              # default view: Landscape dashboard
    ├── projects/
    └── _includes/
```

### Frontend recommendation: 11ty + client-side JSON index
- Nightly Action builds `projects.json` from all YAML files
- Frontend loads it once; filtering is instant client-side
- No backend required; fully static, GitHub Pages compatible
- Upgrade path to Next.js if interactivity demands it later

---

## UX: Default Views

The homepage should feel like a **live dashboard**, not a directory. Three primary views:

1. **The Landscape** *(default)* — visual breakdown of the space: projects by disability area, % active vs. dormant vs. at risk, coverage gaps (areas with few or no projects)
2. **Recent Changes** — what changed in the last 30 days: new projects added, tier changes, activity spikes
3. **Needs Attention** — projects that are valuable but at risk, surfaced as a call to action to the community

The browse/catalog view exists as a tab, not the homepage.

---

## Submission & Governance

- **Who can submit:** Open — anyone can submit a project via GitHub Issues template or PR
- **What gets checked:** Backend automation validates and fetches real status from the source platform; humans do not manually verify maintenance signals
- **What stays manual:** NAUWU indicator, build docs quality assessment, skill level, cost range — fields that require human judgment
- **Data license:** CC0 — no friction for reuse
- **Score methodology:** Fully transparent, versioned in the repo
- **Disputes:** Community can flag incorrect data or dispute a score via Issues

---

## Platform Expansion Roadmap

The `sources` array in the data model means adding a new platform = adding a new fetcher + new source schema block, without touching canonical records.

| Phase | Platforms | Notes |
|---|---|---|
| 1 | GitHub | REST API, token auth |
| 2 | Printables, Thingiverse | Public APIs / scraping |
| 3 | Instructables, Hackaday.io | Scraping or RSS |
| 4 | Zenodo, OSF | DOI resolution, metadata APIs — important for research-affiliated AT projects |
| 5 | EASTIN, GARI | Standards body data, likely manual curation |

---

## Open Questions / Next Decisions

- [ ] **Health score formula** — finalize dimension weights and tier thresholds
- [ ] **Data schema v1** — formalize into a JSON Schema or Pydantic model for validation
- [ ] **Frontend build** — start with 11ty scaffold
- [ ] **Seeding strategy** — what are the first 10–20 projects in the registry?
- [ ] **Primary audience** — builders (contributors, forkers) or AT community (disabled people, clinicians, educators)? This affects score weights, UI language level, and description standards
- [ ] **Domain** — `assistivecommons.watch` or similar
