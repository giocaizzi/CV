"""Tests for cv_builder.cli module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cv_builder.cli import get_package_templates_dir, main


# =============================================================================
# get_package_templates_dir tests
# =============================================================================
@pytest.mark.unit
class TestGetPackageTemplatesDir:
    """Tests for get_package_templates_dir function."""

    def test_returns_path(self):
        """Returns a Path object."""
        result = get_package_templates_dir()
        assert isinstance(result, Path)

    def test_path_contains_templates(self):
        """Path ends with 'templates'."""
        result = get_package_templates_dir()
        assert result.name == "templates"

    def test_path_exists(self):
        """Templates directory exists in package."""
        result = get_package_templates_dir()
        assert result.exists()


# =============================================================================
# main CLI tests
# =============================================================================
@pytest.mark.unit
class TestMainCli:
    """Tests for main CLI entry point."""

    def test_missing_template_exits_with_error(self, monkeypatch, capsys):
        """Missing template causes exit with code 1."""
        monkeypatch.setattr(
            sys, "argv", ["cv-build", "--template", "nonexistent"]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Template" in captured.out
        assert "not found" in captured.out

    def test_missing_data_file_exits_with_error(
        self, monkeypatch, tmp_path, capsys
    ):
        """Missing data file causes exit with code 1."""
        # Create template dir but not data dir
        template_dir = tmp_path / "templates" / "resume"
        template_dir.mkdir(parents=True)

        monkeypatch.setattr(
            sys,
            "argv",
            ["cv-build", "--data", str(tmp_path / "data")],
        )

        # Patch to use our temp templates
        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=tmp_path / "templates",
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Data file not found" in captured.out

    def test_validation_failure_exits_with_error(
        self, monkeypatch, tmp_template_dir, tmp_data_dir, capsys
    ):
        """Schema validation failure causes exit with code 1."""
        # Write invalid data
        invalid_data = '{"invalid": "data"}'
        (tmp_data_dir / "data.json").write_text(invalid_data)

        # Use parent dirs for templates and data
        templates_parent = tmp_template_dir.parent
        data_parent = tmp_data_dir.parent

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cv-build",
                "--template",
                "test_template",
                "--data",
                str(data_parent),
            ],
        )

        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=templates_parent,
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_skip_validation_flag(
        self,
        monkeypatch,
        tmp_template_dir,
        tmp_data_dir,
        capsys,
    ):
        """--skip-validation flag bypasses schema validation."""
        # Write minimal data that wouldn't pass full schema
        minimal_data = """{
            "personalInfo": {"name": "Test"},
            "experience": []
        }"""
        (tmp_data_dir / "data.json").write_text(minimal_data)

        templates_parent = tmp_template_dir.parent
        data_parent = tmp_data_dir.parent

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cv-build",
                "--template",
                "test_template",
                "--data",
                str(data_parent),
                "--skip-validation",
            ],
        )

        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=templates_parent,
        ):
            main()

        captured = capsys.readouterr()
        assert "Done!" in captured.out
        # Validation message should NOT appear
        assert "validates against schema" not in captured.out

    def test_successful_build_without_compile(
        self,
        monkeypatch,
        tmp_template_dir,
        tmp_data_dir,
        sample_cv_data,
        capsys,
    ):
        """Successful build generates .tex file."""
        import json

        (tmp_data_dir / "data.json").write_text(
            json.dumps(sample_cv_data), encoding="utf-8"
        )

        templates_parent = tmp_template_dir.parent
        data_parent = tmp_data_dir.parent

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cv-build",
                "--template",
                "test_template",
                "--data",
                str(data_parent),
                "--skip-validation",
            ],
        )

        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=templates_parent,
        ):
            main()

        captured = capsys.readouterr()
        assert "Generated" in captured.out
        assert "Done!" in captured.out
        assert (tmp_data_dir / "test_template.tex").exists()

    def test_compile_flag_calls_compile_pdf(
        self,
        monkeypatch,
        tmp_template_dir,
        tmp_data_dir,
        sample_cv_data,
        mock_pdflatex,
    ):
        """--compile flag triggers PDF compilation."""
        import json

        (tmp_data_dir / "data.json").write_text(
            json.dumps(sample_cv_data), encoding="utf-8"
        )

        templates_parent = tmp_template_dir.parent
        data_parent = tmp_data_dir.parent

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cv-build",
                "--template",
                "test_template",
                "--data",
                str(data_parent),
                "--skip-validation",
                "--compile",
            ],
        )

        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=templates_parent,
        ):
            main()

        # pdflatex should have been called
        mock_pdflatex.assert_called_once()

    def test_compile_failure_exits_with_error(
        self,
        monkeypatch,
        tmp_template_dir,
        tmp_data_dir,
        sample_cv_data,
        mock_pdflatex_failure,
    ):
        """PDF compilation failure causes exit with code 1."""
        import json

        (tmp_data_dir / "data.json").write_text(
            json.dumps(sample_cv_data), encoding="utf-8"
        )

        templates_parent = tmp_template_dir.parent
        data_parent = tmp_data_dir.parent

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "cv-build",
                "--template",
                "test_template",
                "--data",
                str(data_parent),
                "--skip-validation",
                "--compile",
            ],
        )

        with patch(
            "cv_builder.cli.get_package_templates_dir",
            return_value=templates_parent,
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_default_template_is_resume(self, monkeypatch, capsys):
        """Default template is 'resume'."""
        # This will fail because data doesn't exist, but we can check
        # the error message references 'resume'
        monkeypatch.setattr(
            sys,
            "argv",
            ["cv-build", "--data", "/nonexistent/path"],
        )

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "resume" in captured.out
