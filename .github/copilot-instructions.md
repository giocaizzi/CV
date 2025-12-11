# CV Project - Copilot Instructions

## Project Overview

JSON-driven LaTeX CV system. CV data stored in `cv.json`, validated against `cv-schema.json`, rendered to PDF via LaTeX.

## Stack

- **Data**: JSON with JSON Schema validation
- **Rendering**: LaTeX (pdflatex)
- **Styling**: Custom `CV.sty` package
- **CI**: GitHub Actions (`tex-build.yml`)
- **Dependencies**: TeX Live packages in `requirements.txt`

## Behavior

- Direct, technical, zero filler.
- Correct mistakes immediately with justification.
- Prioritize: correctness → security → maintainability → efficiency.
- Reject unnecessary abstraction, scripts, or automation.
- Produce optimal, production-ready code.
- Resolve queries fully before yielding.

## File Structure

| File | Purpose |
|------|---------|
| `cv.json` | CV data (single source of truth) |
| `cv-schema.json` | JSON Schema for validation |
| `CV.sty` | LaTeX style package with custom commands |
| `giorgio-caizzi.tex` | Main LaTeX document |
| `requirements.txt` | TeX Live package dependencies |

## Rules

### JSON Data (`cv.json`)

- Validate against `cv-schema.json` before committing.
- Use `inResume: boolean` to control LaTeX output inclusion.
- Use `resumeDescription`/`resumeResponsibilities` for shortened resume variants.
- Date format: `Mon. YYYY` or `Mon YYYY`.
- `endDate: null` indicates current/ongoing.

### LaTeX (`CV.sty`, `*.tex`)

- Use custom commands defined in `CV.sty`.
- Keep styling in `CV.sty`, content in `.tex` files.
- Update version in `CV.sty` on changes.
- Test compilation locally with `pdflatex`.

### Schema (`cv-schema.json`)

- `additionalProperties: false` enforced—no undeclared fields.
- Update schema when adding new CV fields.
- Required fields vary by section—check schema before editing.

## Workflow

1. Edit `cv.json` for content changes.
2. Update `giorgio-caizzi.tex` if structure changes.
3. Modify `CV.sty` for styling changes.
4. Run `pdflatex giorgio-caizzi.tex` to compile.
5. CI validates on push to `main`.

## Prohibited

- Raw content in `.tex` files that should be in `cv.json`.
- Schema violations in `cv.json`.
- Undocumented LaTeX commands.
