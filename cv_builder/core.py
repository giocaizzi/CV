"""Core CV building functionality."""

import json
import subprocess
from pathlib import Path

import jsonschema
from jinja2 import Environment, FileSystemLoader


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
    """Escape special LaTeX characters."""
    if not isinstance(text, str):
        return text
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
    return text


def format_date_range(start: str, end: str | None) -> str:
    """Format date range for display. None end means 'Present'."""
    if end is None:
        return start
    return f"{start} -- {end}"


def filter_by_resume(items: list) -> list:
    """Filter items by inResume flag."""
    return [item for item in items if item.get("inResume", True)]


def get_responsibilities(item: dict) -> list:
    """Get responsibilities filtered by inResume flag.

    Each responsibility is an object with 'value' and 'inResume' fields.
    Returns list of responsibility strings where inResume=true.
    """
    responsibilities = item.get("responsibilities", [])
    return [r["value"] for r in responsibilities if r.get("inResume", True)]


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
    env.filters["get_resp"] = get_responsibilities

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


def compile_pdf(tex_file: Path, template_dir: Path) -> bool:
    """Compile LaTeX to PDF using pdflatex."""
    output_dir = tex_file.parent
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
