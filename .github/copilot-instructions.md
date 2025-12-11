# CV Project - Copilot Instructions

## Project Overview

JSON-driven LaTeX CV with Jinja2 templating. Self-contained templates in `templates/<name>/`.

## Stack

- **Data**: JSON with JSON Schema validation
- **Templating**: Jinja2 (Python) with custom delimiters
- **Rendering**: LaTeX (pdflatex)
- **Build**: `build.py` orchestrates validation + templating

## Structure

```
templates/<name>/
├── data.json        # CV data (single source of truth)
├── schema.json      # JSON Schema for validation
├── template.tex.j2  # Jinja2 LaTeX template
├── <name>.sty       # LaTeX styling
├── <name>.tex       # Generated output (tracked)
└── <name>.pdf       # Compiled PDF (tracked)
```

## Rules

### JSON Data

- All elements have `inResume: boolean` for visibility control
- `description` for resume, `longDescription` for full version
- Date format: `Mon. YYYY` or `Mon YYYY`
- `endDate: null` = current/ongoing

### Schema

- `additionalProperties: false` enforced
- Update schema when adding new fields

## Workflow

```bash
python build.py                 # Generate .tex
python build.py --compile       # Generate and compile PDF
python build.py --variant name  # Build specific variant
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

## Prohibited

- Raw content in templates that should be in data.json
- Schema violations
- Editing generated files in output/
