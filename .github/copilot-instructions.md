# CV Project - Copilot Instructions

## Project Overview

JSON-driven LaTeX CV with Jinja2 templating.

## Stack

- **Data**: JSON with JSON Schema validation
- **Templating**: Jinja2 (Python) with custom delimiters
- **Rendering**: LaTeX (pdflatex)
- **Build**: `cv-build` CLI orchestrates validation + templating

## Structure

```
cv_builder/templates/<name>/   # Package templates
├── schema.json                # JSON Schema for validation
├── template.tex.j2            # Jinja2 LaTeX template
└── <name>.sty                 # LaTeX styling

data/<name>/                   # User data
└── data.json                  # CV data (single source of truth)

output/<name>/                 # Generated files
├── <name>.tex                 # Generated output (tracked)
└── <name>.pdf                 # Compiled PDF (tracked)
```

## Rules

### Python

- Use `poetry` for dependency management and version tracking

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
poetry run cv-build                         # Generate .tex
poetry run cv-build --compile               # Generate and compile PDF
poetry run cv-build --variant name          # Build specific variant
poetry run cv-build --data /path --output /path  # Custom paths
```

## Jinja2 Syntax

Custom delimiters (LaTeX-safe):
- Variables: `<< cv.field >>`
- Blocks: `<% for item in list %>`
- Comments: `<# comment #>`

Filters:
- `| latex` — escape LaTeX special characters
- `| date_range` — format start/end dates
- `| get_resp` — get visible responsibilities

## Latex

- Keep `.sty` files versioned via header comments.

## Prohibited

- Raw content in templates that should be in data.json
- Schema violations
- Editing generated files in output/
