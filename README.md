# CV Builder

[![Build CV](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml/badge.svg)](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml)

JSON-driven LaTeX CV building with Jinja2 templating.

📄 [Download CV](https://raw.githubusercontent.com/giocaizzi/CV/main/data/resume.pdf)

## 📁 Structure

```
cv_builder/
├── schema.json                # JSON Schema validation (single, top-level)
└── templates/resume/          # Template rendering assets
    ├── template.tex.j2        # Jinja2 LaTeX template
    └── resume.sty             # LaTeX styling

data/
├── cv.json                    # CV data (editable, template-agnostic)
├── resume.tex                 # Generated (tracked)
├── resume.pdf                 # Compiled (tracked)
└── cv.jsonresume.json         # Vanilla JSON Resume artifact (tracked, auto-emitted)
```

## 🚀 Usage

Install dependencies and view help:

```bash
# Activate virtual environment
source .venv/bin/activate
poetry install
cv-build --help
```

**Examples**:

```bash
cv-build                              # Build default template + emit cv.jsonresume.json
cv-build --compile                    # Build and compile to PDF
cv-build --template resume --compile  # Explicit template
cv-build --data ~/mydata              # Custom data path
cv-build --no-emit-jsonresume         # Skip JSON Resume artifact
```

The project is compatible with the [JSON Resume](https://jsonresume.org) ecosystem.
`cv-build` automatically emits a vanilla `data/cv.jsonresume.json` artifact on
every run, suitable for hosting on `registry.jsonresume.org` or feeding into
any of the 400+ JSON Resume themes.

### ✏️ Editing and building on-the-fly

Edit `data/cv.json` directly on GitHub (web/mobile). CI automatically rebuilds and commits the updated PDF.

## 📋 Requirements

- Python 3.10+
- TeX Live / TinyTeX / MacTeX