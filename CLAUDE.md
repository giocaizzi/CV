# Project Overview

JSON-driven LaTeX CV with Jinja2 templating.

## Stack

- **Data**: JSON with JSON Schema validation
- **Templating**: Jinja2 (Python) with custom delimiters
- **Rendering**: LaTeX (pdflatex)
- **Build**: `cv-build` CLI orchestrates validation + templating

## Structure

```
cv_builder/
├── schema.json                # JSON Schema for validation (single, top-level)
└── templates/<name>/          # Package templates (per-template rendering assets)
    ├── template.tex.j2        # Jinja2 LaTeX template
    └── <name>.sty             # LaTeX styling

data/
├── cv.json                    # CV data (single source of truth, template-agnostic)
├── <name>.tex                 # Generated output (named after template, tracked)
├── <name>.pdf                 # Compiled PDF (named after template, tracked)
└── cv.jsonresume.json         # Vanilla JSON Resume artifact (tracked, auto-emitted)
```

## Rules

### Python

- Use `poetry` for dependency management and version tracking

#### Python tests

- Use `pytest` for unit tests
- Use Test-Driven Development (TDD) approach, writing tests before code
- When fixing bugs, write a test that reproduces the bug first, only then fix the bug and verify the test passes
- Tests behaviour, not implementation details
- Consider edge cases and invalid, missing data
- Mark tests with `@pytest.mark.unit` (fast, mocked) or `@pytest.mark.integration` (real I/O)

```bash
poetry run pytest                    # Run all tests
poetry run pytest -m unit            # Run unit tests only
poetry run pytest -m integration     # Run integration tests only
poetry run pytest --cov=cv_builder   # Run with coverage report
```

### JSON Data

- The source schema is a pragmatic superset of [JSON Resume](https://jsonresume.org):
  field names are vanilla (`basics`, `work`, `education`, `certificates`,
  `projects`, etc.), augmented with `x-` extension fields for CV-specific
  curation (`x-inResume`, `x-longSummary`, `x-technologies`, `x-details`,
  `x-projects`).
- Curation flags: every element has `x-inResume: boolean` for visibility
  control on the printed resume.
- Short vs full: `summary` (printed) and `x-longSummary` (full version, not
  printed). For experience entries, `highlights` are objects
  `{value, x-inResume}` so each bullet is individually toggleable.
- Date format: **ISO 8601** in the source — `"2024-05"` (month) or `"2023"`
  (year-only for certificates). A `| month_year` Jinja filter renders them
  as `Mon YYYY` for LaTeX.
- `basics.location` is the canonical JSON Resume object shape:
  `{city, countryCode, region?, address?, postalCode?}`. A `| location_str`
  Jinja filter joins it into `"City, Country"` for LaTeX, with country code
  lookup in `COUNTRY_NAMES` (extend as needed).
- `endDate: null` = current/ongoing in the source. The JSON Resume emitter
  drops the key entirely for the vanilla artifact (vanilla doesn't permit
  `null`).

### JSON Schema

- `additionalProperties: false` enforced
- Update schema when adding new fields

## Workflow

```bash
poetry install                              # Install dependencies
poetry run cv-build                         # Generate .tex + cv.jsonresume.json
poetry run cv-build --compile               # Generate and compile PDF
poetry run cv-build --template name         # Build specific template
poetry run cv-build --data /path            # Custom data path
poetry run cv-build --skip-validation       # Skip JSON schema validation
poetry run cv-build --no-emit-jsonresume    # Skip cv.jsonresume.json emission
```

### CI / publish flow

- `test.yml` runs unit + integration tests on every PR against `main`
  across Python 3.10–3.13.
- `tex-build.yml` runs on every PR against `main` that touches CV-relevant
  files (`data/cv.json`, `cv_builder/**`, `latex_requirements.txt`). It
  regenerates `.tex` / `.pdf` / `cv.jsonresume.json` and commits them back
  to the PR head branch — so the rendered PDF is part of review.
- Merging the PR publishes the rebuilt artifacts to `main`. No bot push
  to `main`; works under a "require PR" ruleset without bypass.

## JSON Resume compatibility

The source schema is a pragmatic superset of the JSON Resume specification:
it uses standard JSON Resume field names (`basics`, `work`, `education`, etc.)
augmented with `x-` extension fields (`x-inResume`, `x-longSummary`,
`x-details`, etc.) for CV-specific visibility control and extra data.

`cv-build` always emits a vanilla JSON Resume artifact (`data/cv.jsonresume.json`)
alongside the `.tex` output. The emitter (in `cv_builder/jsonresume.py`):

- Filters to items where `x-inResume` is `true` (matching the printed output)
- Strips all `x-*` keys recursively
- Flattens `work[*].highlights` from `[{value, x-inResume}]` to `["string"]`
- Converts `technicalSkills`/`personalSkills` object-maps to a single `skills[]`
  array of `{name, keywords[]}` entries
- Drops `meta.footer` and `work[*].x-projects` (no vanilla equivalent)

This enables hosting on `registry.jsonresume.org` and feeding into the 400+
JSON Resume themes.

## Jinja2 Syntax

Custom delimiters (LaTeX-safe):
- Variables: `<< cv.field >>`
- Blocks: `<% for item in list %>`
- Comments: `<# comment #>`

Filters (registered in `cv_builder/core.py::create_jinja_env`):
- `| latex` — escape LaTeX special characters (supports `/latex{...}` for raw LaTeX)
- `| date_range` — format `{startDate, endDate}` as `"Mon YYYY -- Mon YYYY"` (or just start if `endDate` is null)
- `| month_year` — convert an ISO `"YYYY-MM"` string to `"Mon YYYY"` for display
- `| location_str` — convert a JSON Resume location object to `"City, Region, Country"`
- `| resume_filter` — filter a list of items by `x-inResume`
- `| get_highlights` — get visible highlights (objects → list of `value` strings, filtered by `x-inResume`)

### Raw LaTeX in JSON data

Use `/latex{...}` syntax to include raw LaTeX that won't be escaped:

```json
{
  "value": "Python /latex{\\&} SQL",
  "skills": "Use /latex{\\textbf{bold}} for emphasis"
}
```

This outputs `Python & SQL` and `Use \textbf{bold} for emphasis` in LaTeX.

## Latex

- Keep `.sty` files versioned via header comments.
