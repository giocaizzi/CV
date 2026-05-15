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

- All elements have `inResume: boolean` for visibility control
- `description` for resume, `longDescription` for full version
- Date format: `Mon. YYYY` or `Mon YYYY`
- `endDate: null` = current/ongoing

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
poetry run cv-build --no-emit-jsonresume    # Skip cv.jsonresume.json emission
```

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

Filters:
- `| latex` — escape LaTeX special characters (supports `/latex{...}` for raw LaTeX)
- `| date_range` — format start/end dates
- `| get_resp` — get visible responsibilities

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
