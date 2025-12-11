"""CLI entry point for CV Builder."""

import argparse
import sys
from pathlib import Path

from .core import build_variant, compile_pdf, load_json, validate_cv


def get_package_templates_dir() -> Path:
    """Get the templates directory from the package."""
    return Path(__file__).parent / "templates"


def get_data_dir() -> Path:
    """Get the data directory relative to cwd."""
    return Path.cwd() / "data"


def get_output_dir() -> Path:
    """Get the output directory relative to cwd."""
    return Path.cwd() / "output"


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cv-build",
        description="Build CV variant from JSON data and Jinja2 templates",
    )
    parser.add_argument(
        "--variant",
        "-v",
        default="resume",
        help="Variant to build (default: resume)",
    )
    parser.add_argument(
        "--compile",
        "-c",
        action="store_true",
        help="Compile to PDF after generating",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip JSON schema validation",
    )
    args = parser.parse_args()

    templates_dir = get_package_templates_dir()
    data_dir = get_data_dir()
    output_dir = get_output_dir()

    # Paths for this variant
    template_variant_dir = templates_dir / args.variant
    data_file = data_dir / args.variant / "data.json"
    schema_file = template_variant_dir / "schema.json"
    output_variant_dir = output_dir / args.variant

    if not template_variant_dir.exists():
        print(f"✗ Variant '{args.variant}' not found at {template_variant_dir}")
        sys.exit(1)

    if not data_file.exists():
        print(f"✗ Data file not found at {data_file}")
        sys.exit(1)

    # Ensure output directory exists
    output_variant_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Building variant: {args.variant}")
    cv_data = load_json(data_file)

    # Validate
    if not args.skip_validation:
        schema = load_json(schema_file)
        if not validate_cv(cv_data, schema):
            sys.exit(1)

    # Build
    tex_file = build_variant(
        template_variant_dir, output_variant_dir, args.variant, cv_data
    )

    # Compile
    if args.compile:
        if not compile_pdf(tex_file, template_variant_dir):
            sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
