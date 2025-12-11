# CV

[![Build CV](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml/badge.svg)](https://github.com/giocaizzi/CV/actions/workflows/tex-build.yml)

JSON-driven LaTeX CV with Jinja2 templating.

## Structure

```
templates/resume/
├── data.json        # CV data
├── schema.json      # JSON Schema validation
├── template.tex.j2  # Jinja2 LaTeX template
├── resume.sty       # LaTeX styling
├── resume.tex       # Generated (tracked)
└── resume.pdf       # Generated (tracked)
```

## Usage

### Local build

```bash
pip install -r requirements.txt
# Help
python build.py --help
# Build and compile to PDF
python build.py --compile            # Build and compile PDF
python build.py --variant resume     # Build specific variant
python build.py --variant resume --compile  # Build and compile specific variant
```

### Mobile editing

Edit `templates/resume/data.json` directly on GitHub (web/mobile). CI automatically rebuilds and commits the updated PDF.

## Requirements

- Python 3.10+
- TeX Live / TinyTeX / MacTeX