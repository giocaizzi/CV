# CV Builder

[![Build CV](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml/badge.svg)](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml)

JSON-driven LaTeX CV building with Jinja2 templating.

[Download CV](https://raw.githubusercontent.com/giocaizzi/CV/main/output/resume/resume.pdf)

## Structure

```
cv_builder/templates/resume/   # Package templates (versioned)
├── schema.json                # JSON Schema validation
├── template.tex.j2            # Jinja2 LaTeX template
└── resume.sty                 # LaTeX styling

data/resume/                   # User data
└── data.json                  # CV data (editable)

output/resume/                 # Generated files
├── resume.tex                 # Generated (tracked)
└── resume.pdf                 # Compiled (tracked)
```

## Usage

### Local build

```bash
poetry install
poetry run cv-build --help
```

### Examples

```bash
cv-build                              # Build default variant
cv-build --compile                    # Build and compile to PDF
cv-build --variant resume --compile   # Explicit variant
cv-build --data ~/mydata --output ~/out  # Custom paths
```

### Editing aand building on-the-fly

Edit `data/resume/data.json` directly on GitHub (web/mobile). CI automatically rebuilds and commits the updated PDF.

## Requirements

- Python 3.10+
- TeX Live / TinyTeX / MacTeX