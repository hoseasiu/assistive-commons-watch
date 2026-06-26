# Assistive Commons Watch

An automated health dashboard for open-source assistive technology projects.

**[Live site →](https://hoseasiu.github.io/assistive-commons-watch/)**

---

ACW is a report card for open-source AT. For each project it checks:

- **Is it still being maintained?** (recent commits, issue response, releases)
- **Can you actually build or replicate it?** (parts lists, build docs, fabrication files, estimated cost)
- **Was it designed with disabled people's input?** ("Nothing About Us Without Us")
- **Is there documentation for end users** — not just developers?
- **Is the community welcoming** to new contributors?

Generic open-source health tools don't ask the AT-specific questions. ACW does. The result is a filterable, queryable registry that shows you which projects are worth your time — whether you're a physical therapist hunting for a tool that actually has user docs, a high school maker looking for a hardware project to fork, or a software engineer wanting to contribute to something that matters.

## What it tracks

Each project record captures:

- **Identity** — name, description, disability area, modality (hardware / software / firmware / hybrid), interfaces
- **Activity signals** — last commit, issue response rate, release cadence (auto-fetched by the fetch workflow)
- **Replicability** — BOM presence, build docs quality, fabrication methods, estimated cost, release artifacts
- **AT-specific signals** — "Nothing About Us Without Us" (NAUWU) indicator, end-user documentation, feedback channels, known deployed instances
- **Community health** — CONTRIBUTING.md, issue templates, code of conduct
- **Provenance** — license, associated publications, institutional affiliation, originating program

## Health scoring

Every project gets a weighted score (0–10) across five dimensions:

```
score = 0.25×activity + 0.30×replicability + 0.15×community + 0.20×at_specific + 0.10×provenance
```

Replicability is weighted highest because a well-documented dormant project can still save a clinician months of work. Scores map to tiers (first matching rule wins):

| Tier | Condition | Meaning |
|------|-----------|---------|
| Archived | activity = 0 and last commit > 3 years ago | Explicitly archived or clearly abandoned |
| Thriving | score ≥ 7.5 | Active, documented, welcoming |
| Stable | score ≥ 5.5 | Works, maintained passively, usable |
| Dormant | activity ≤ 2 and replicability ≥ 5 | Not recently active but documented enough to replicate |
| At Risk | (everything else) | Useful but maintenance unclear or documentation gaps |
| Documented | static platform only (Instructables, Printables, etc.) | Build-readiness signals shown; no live health score |
| Unverified | no sources fetched yet | Newly submitted, not yet assessed |

**Platform precedence for scoring:** GitHub signals are used when present. If a project has no GitHub source, Hackaday.io signals are used. Static platforms (Instructables, Printables, Thingiverse, MyMiniFactory) fall back next. Projects with no sources at all get `unverified`. Static-platform projects skip the community dimension (no meaningful signal) and are always assigned the `documented` tier.

## Repo layout

```
_data/projects/       one YAML file per project (source of truth)
_fetchers/            Python: Pydantic models, GitHub REST fetcher, health-scoring engine
scripts/
  validate_yaml.py    validates all YAMLs against the Pydantic model
  export_schema.py    regenerates schema.json (do not hand-edit)
  build_json.py       reads YAMLs → writes site/_data/acw.json for the frontend
site/                 Eleventy (11ty) frontend source
  index.njk           Landscape homepage (three-tab dashboard)
schema.json           CI artifact — do not edit by hand
```

## Development

**Prerequisites:** Python 3.11+, Node.js

```bash
# Python setup
pip install -e .

# Node setup
npm install

# Build site data from YAMLs (required before serving)
python scripts/build_json.py

# Serve locally at http://localhost:8080
npm run serve

# Production build → _site/
npm run build
```

## Adding a project

Projects live as YAML files in `_data/projects/`. The Pydantic model in [`_fetchers/models.py`](_fetchers/models.py) is the authoritative schema.

1. Copy an existing YAML from `_data/projects/` as a starting point
2. Fill in the canonical fields (identity, replicability, AT-specific signals)
3. Add a `sources` entry — `platform: github` for GitHub projects; `platform: instructables`, `printables`, `thingiverse`, `myminifactory`, or `hackaday` for other platforms
4. Run `python scripts/validate_yaml.py` to check your file (pass a path to validate a single file; run with no args to validate all)
5. Open a PR — CI will validate the schema and check `schema.json` is current

`validate_yaml.py` treats missing `iso_9999_codes` or an unset `at_relevance` as warnings (not errors) — these show up in the output but won't block CI.

The `disability_area` field is ordered: the first entry is used as the primary display area on the Landscape page.

Fields written by the fetch workflow (`health_tier`, `health_score`, activity signals) will be overwritten automatically — you don't need to set them.

## CI

- **On PR** (`validate.yml`) — validates all project YAMLs against the Pydantic schema and checks that `schema.json` is up to date
- **On merge** (`deploy.yml`) — builds and deploys the site to GitHub Pages

## Data license

Project data is [CC0](https://creativecommons.org/publicdomain/zero/1.0/) — no friction for reuse. The scoring methodology is fully transparent and versioned in this repo.

## Architecture notes

- `site/_data/acw.json` is generated by `scripts/build_json.py` — do not edit it directly. The script pre-aggregates everything the frontend needs (`by_area`, `tier_counts`, `needs_attention`, `recently_added`, stats) so 11ty templates do no runtime computation. If a YAML already has `health_tier`/`health_score` written by the fetch workflow, those stored values are used; otherwise scores are computed live from the static fields.
- `schema.json` is generated by `scripts/export_schema.py` (calls Pydantic's `model_json_schema()`) — do not edit it directly
- The site is deployed to `hoseasiu.github.io/assistive-commons-watch/`; JavaScript that builds links dynamically must use the `env.pathPrefix` global rather than hardcoded absolute paths (see [`CLAUDE.md`](CLAUDE.md) for details)

## Platform roadmap

The `sources` array in each YAML is designed for multi-platform expansion: adding a new platform means adding a new fetcher, not touching canonical records.

| Status | Platforms |
|--------|-----------|
| Implemented | GitHub, Instructables, Printables, Thingiverse, MyMiniFactory, Hackaday.io |
| Planned | Zenodo, OSF, EASTIN, GARI |
