"""Core CV building functionality."""

import json
import subprocess
from pathlib import Path

import jsonschema
from jinja2 import Environment, FileSystemLoader

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_json(path: Path) -> dict:
    """Load and parse JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_cv(cv_data: dict, schema: dict) -> bool:
    """Validate CV data against JSON schema."""
    try:
        jsonschema.validate(instance=cv_data, schema=schema)
        print("✓ CV data validates against schema")
        return True
    except jsonschema.ValidationError as e:
        print(f"✗ Schema validation failed: {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.absolute_path)}")
        return False


def latex_escape(text: str) -> str:
    """Escape special LaTeX characters.

    Supports raw LaTeX passthrough using /latex{...} syntax.
    Content inside /latex{...} will not be escaped.

    Example:
        "Python /latex{\\&} SQL" -> "Python & SQL"
        "Use /latex{\\textbf{bold}} text" -> "Use \\textbf{bold} text"
    """
    import re

    if not isinstance(text, str):
        return text

    # Pattern to match /latex{...} with balanced braces (one level deep)
    # Allows any characters including backslashes, with nested braces one level deep
    pattern = r"/latex\{((?:[^{}]|\{[^{}]*\})*)\}"

    # Find all raw LaTeX sections and store them with placeholders
    raw_sections = []

    def store_raw(match):
        idx = len(raw_sections)
        raw_sections.append(match.group(1))
        # Use null bytes as placeholder - won't appear in normal text
        return f"\x00\x01{idx}\x02\x00"

    # Replace raw LaTeX sections with placeholders
    text = re.sub(pattern, store_raw, text)

    # Escape the remaining text
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, escape in replacements.items():
        text = text.replace(char, escape)

    # Restore raw LaTeX sections
    for i, raw in enumerate(raw_sections):
        text = text.replace(f"\x00\x01{i}\x02\x00", raw)

    return text


def format_month_year(iso_date: str) -> str:
    """Convert ISO 8601 date string to display format.

    "2024-05" -> "May 2024"
    "2020-07" -> "Jul 2020"
    "2023"    -> "2023"  (year-only)
    ""        -> ""
    None      -> ""
    """
    if not iso_date:
        return ""
    iso_date = str(iso_date).strip()
    if not iso_date:
        return ""
    parts = iso_date.split("-")
    if len(parts) == 1:
        # Year-only
        return parts[0]
    year = parts[0]
    try:
        month_idx = int(parts[1]) - 1
        month = MONTH_NAMES[month_idx]
    except (ValueError, IndexError):
        return iso_date
    return f"{month} {year}"


def format_date_range(start: str, end: str | None) -> str:
    """Format date range for display. None end means 'Present'."""
    start_fmt = format_month_year(start)
    if end is None:
        return start_fmt
    end_fmt = format_month_year(end)
    return f"{start_fmt} -- {end_fmt}"


def filter_by_resume(items: list) -> list:
    """Filter items by x-inResume flag."""
    return [item for item in items if item.get("x-inResume", True)]


def get_highlights(item: dict) -> list:
    """Get highlights filtered by x-inResume flag.

    Each highlight is an object with 'value' and 'x-inResume' fields.
    Returns list of highlight strings where x-inResume=true.
    """
    highlights = item.get("highlights", [])
    return [h["value"] for h in highlights if h.get("x-inResume", True)]


def create_jinja_env(variant_dir: Path) -> Environment:
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(variant_dir),
        autoescape=False,  # LaTeX, not HTML
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="<<",
        variable_end_string=">>",
        comment_start_string="<#",
        comment_end_string="#>",
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Custom filters
    env.filters["latex"] = latex_escape
    env.filters["date_range"] = lambda item: format_date_range(
        item.get("startDate", ""), item.get("endDate")
    )
    env.filters["resume_filter"] = filter_by_resume
    env.filters["get_highlights"] = get_highlights
    env.filters["month_year"] = format_month_year

    return env


def build_variant(
    template_dir: Path, output_dir: Path, variant_name: str, cv_data: dict
) -> Path:
    """Render a variant template with CV data."""
    env = create_jinja_env(template_dir)
    template = env.get_template("template.tex.j2")

    # Render
    output = template.render(cv=cv_data)

    # Write output to output directory
    output_file = output_dir / f"{variant_name}.tex"
    output_file.write_text(output, encoding="utf-8")

    print(f"✓ Generated {output_file}")
    return output_file


def build_jsonresume(cv_data: dict, output_path: Path) -> Path:
    """Emit vanilla JSON Resume artifact alongside the .tex output."""
    from .jsonresume import to_jsonresume
    vanilla = to_jsonresume(cv_data)
    output_path.write_text(
        json.dumps(vanilla, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Generated {output_path}")
    return output_path


def compile_pdf(tex_file: Path, template_dir: Path) -> bool:
    """Compile LaTeX to PDF using pdflatex."""
    tex_file = tex_file.resolve()
    output_dir = tex_file.parent.resolve()
    print(f"  Compiling {tex_file.name}...")

    # Copy .sty file to output directory for compilation
    import shutil
    for sty_file in template_dir.glob("*.sty"):
        shutil.copy(sty_file, output_dir / sty_file.name)

    try:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                str(output_dir),
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            cwd=output_dir,
        )
        if result.returncode == 0:
            pdf_file = tex_file.with_suffix(".pdf")
            print(f"✓ Compiled {pdf_file}")
            return True
        else:
            print("✗ Compilation failed")
            output = result.stdout
            print(output[-2000:] if len(output) > 2000 else output)
            return False
    except FileNotFoundError:
        print("✗ pdflatex not found. Install TeX Live or MacTeX.")
        return False
