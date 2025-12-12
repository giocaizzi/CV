"""Integration tests for cv_builder package.

These tests use real file I/O and the actual package templates.
LaTeX compilation is skipped (requires TeX installation).
"""

from pathlib import Path

import pytest

from cv_builder.cli import get_package_templates_dir
from cv_builder.core import (
    build_variant,
    create_jinja_env,
    load_json,
    validate_cv,
)


@pytest.mark.integration
class TestLoadValidateBuildFlow:
    """Integration tests for load -> validate -> build flow."""

    def test_full_flow_with_sample_data(self, sample_cv_data, tmp_path):
        """Complete flow: load schema, validate data, build .tex."""
        # Setup
        template_dir = get_package_templates_dir() / "resume"
        schema = load_json(template_dir / "schema.json")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Validate
        is_valid = validate_cv(sample_cv_data, schema)
        assert is_valid is True

        # Build
        tex_file = build_variant(
            template_dir, output_dir, "resume", sample_cv_data
        )

        # Verify
        assert tex_file.exists()
        content = tex_file.read_text()
        assert "Software Engineer" in content
        assert "Tech Corp" in content

    def test_flow_with_real_data_file(self, tmp_path):
        """Test with actual data/resume/data.json if available."""
        project_root = Path(__file__).parent.parent
        data_file = project_root / "data" / "resume" / "data.json"
        template_dir = get_package_templates_dir() / "resume"

        if not data_file.exists():
            pytest.skip("Real data file not available")

        # Load and validate
        cv_data = load_json(data_file)
        schema = load_json(template_dir / "schema.json")
        assert validate_cv(cv_data, schema) is True

        # Build
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        tex_file = build_variant(template_dir, output_dir, "resume", cv_data)

        assert tex_file.exists()
        assert tex_file.stat().st_size > 0


@pytest.mark.integration
class TestJinjaEnvironmentIntegration:
    """Integration tests for Jinja2 environment with real templates."""

    def test_template_loads_and_renders(self, sample_cv_data):
        """Real template loads and renders without errors."""
        template_dir = get_package_templates_dir() / "resume"
        env = create_jinja_env(template_dir)

        template = env.get_template("template.tex.j2")
        output = template.render(cv=sample_cv_data)

        # Basic sanity checks
        assert len(output) > 100
        assert "Software Engineer" in output

    def test_latex_escaping_in_template(self):
        """LaTeX special characters are escaped where filter applied."""
        template_dir = get_package_templates_dir() / "resume"
        env = create_jinja_env(template_dir)
        template = env.get_template("template.tex.j2")

        # Data with special characters in location field (which uses | latex)
        cv_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "test@example.com",
                "location": "City & State",
                "linkedin": {
                    "url": "https://linkedin.com/in/test",
                    "inResume": True,
                },
                "github": {
                    "url": "https://github.com/test",
                    "inResume": True,
                },
            },
            "experience": [
                {
                    "title": "Engineer",
                    "company": "Tech Co",
                    "location": "New York & LA",  # location uses | latex
                    "startDate": "Jan 2020",
                    "endDate": None,
                    "description": "Work",
                    "responsibilities": [],
                    "inResume": True,
                }
            ],
            "education": [],
            "licenses": [],
            "technicalSkills": {},
            "projects": [],
            "personalSkills": {},
            "footer": {"value": "", "inResume": False},
        }

        output = template.render(cv=cv_data)

        # Location field has | latex filter applied
        assert r"New York \& LA" in output

    def test_raw_latex_passthrough_in_template(self):
        """Raw /latex{} syntax passes through unescaped."""
        template_dir = get_package_templates_dir() / "resume"
        env = create_jinja_env(template_dir)
        template = env.get_template("template.tex.j2")

        cv_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "test@example.com",
                "location": "City",
                "linkedin": {
                    "url": "https://linkedin.com/in/test",
                    "inResume": True,
                },
                "github": {
                    "url": "https://github.com/test",
                    "inResume": True,
                },
            },
            "experience": [],
            "education": [],
            "licenses": [],
            "technicalSkills": {
                "Languages": {
                    "value": r"Python /latex{\&} SQL",
                    "inResume": True,
                }
            },
            "projects": [],
            "personalSkills": {},
            "footer": {"value": "", "inResume": False},
        }

        output = template.render(cv=cv_data)

        # Raw LaTeX should pass through as \& (not \\&)
        assert r"Python \& SQL" in output


@pytest.mark.integration
class TestSchemaValidation:
    """Integration tests for JSON schema validation."""

    def test_real_schema_validates_sample_data(
        self, sample_cv_data, valid_schema
    ):
        """Real schema validates the sample CV data."""
        assert validate_cv(sample_cv_data, valid_schema) is True

    def test_schema_rejects_extra_properties(self, valid_schema):
        """Schema rejects data with extra properties."""
        invalid_data = {
            "personalInfo": {
                "name": "John",
                "email": "john@example.com",
                "location": "NYC",
                "linkedin": {
                    "url": "https://linkedin.com/in/john",
                    "inResume": True,
                },
                "github": {
                    "url": "https://github.com/john",
                    "inResume": True,
                },
                "extraField": "not allowed",  # Should fail
            },
            "experience": [],
            "education": [],
            "licenses": [],
            "technicalSkills": [],
            "projects": [],
            "personalSkills": [],
        }

        assert validate_cv(invalid_data, valid_schema) is False

    def test_schema_requires_all_sections(self, valid_schema):
        """Schema requires all top-level sections."""
        incomplete_data = {
            "personalInfo": {
                "name": "John",
                "email": "john@example.com",
                "location": "NYC",
                "linkedin": {
                    "url": "https://linkedin.com/in/john",
                    "inResume": True,
                },
                "github": {
                    "url": "https://github.com/john",
                    "inResume": True,
                },
            },
            # Missing: experience, education, licenses, etc.
        }

        assert validate_cv(incomplete_data, valid_schema) is False


@pytest.mark.integration
class TestOutputFileGeneration:
    """Integration tests for output file generation."""

    def test_generates_valid_latex_structure(self, sample_cv_data, tmp_path):
        """Generated .tex file has valid LaTeX structure."""
        template_dir = get_package_templates_dir() / "resume"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        tex_file = build_variant(
            template_dir, output_dir, "resume", sample_cv_data
        )
        content = tex_file.read_text()

        # Basic LaTeX structure checks
        assert r"\documentclass" in content
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_output_encoding_is_utf8(self, sample_cv_data, tmp_path):
        """Output file uses UTF-8 encoding."""
        # Add UTF-8 characters to data
        sample_cv_data["personalInfo"]["name"] = "José García"

        template_dir = get_package_templates_dir() / "resume"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        tex_file = build_variant(
            template_dir, output_dir, "resume", sample_cv_data
        )

        # Should read without encoding errors
        content = tex_file.read_text(encoding="utf-8")
        assert "José García" in content
