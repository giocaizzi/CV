# CV Builder

[![Build CV](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml/badge.svg)](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml)

JSON-driven LaTeX CV building with Jinja2 templating.

📄 [Download CV](https://raw.githubusercontent.com/giocaizzi/CV/main/data/resume/resume.pdf)

## 📁 Structure

```
cv_builder/templates/resume/   # Package templates (versioned)
├── schema.json                # JSON Schema validation
├── template.tex.j2            # Jinja2 LaTeX template
└── resume.sty                 # LaTeX styling

data/resume/                   # User data + generated output
├── resume.json                # CV data (editable)
├── resume.tex                 # Generated (tracked)
└── resume.pdf                 # Compiled (tracked)
```

## 🚀 Usage

Install dependencies and view help:

```bash
uv sync
source .venv/bin/activate
cv-build --help
```

**Examples**:

```bash
cv-build                              # Build default template
cv-build --compile                    # Build and compile to PDF
cv-build --template resume --compile  # Explicit template
cv-build --data ~/mydata              # Custom data path
```

### ✏️ Editing and building on-the-fly

Edit `data/resume/resume.json` directly on GitHub (web/mobile). CI automatically rebuilds and commits the updated PDF.

## 📋 Requirements

- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- TeX Live / TinyTeX / MacTeX