"""Shared pytest fixtures for cv_builder tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_cv_data() -> dict:
    """Minimal valid CV data for testing."""
    return {
        "personalInfo": {
            "name": "John Doe",
            "email": "john@example.com",
            "location": "New York, NY",
            "linkedin": {
                "url": "https://linkedin.com/in/johndoe",
                "inResume": True,
            },
            "github": {
                "url": "https://github.com/johndoe",
                "inResume": True,
            },
        },
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "New York, NY",
                "startDate": "Jan 2020",
                "endDate": None,
                "description": "Building software",
                "responsibilities": [
                    {"value": "Write code", "inResume": True},
                    {"value": "Review PRs", "inResume": False},
                ],
                "inResume": True,
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "institution": "State University",
                "location": "Boston, MA",
                "startDate": "Sep 2016",
                "endDate": "May 2020",
                "details": {},
                "inResume": True,
            }
        ],
        "licenses": [],
        "technicalSkills": {
            "Languages": {
                "value": "Python, JavaScript",
                "inResume": True,
            }
        },
        "projects": [
            {
                "name": "Open Source Tool",
                "description": "A CLI tool",
                "technologies": "Python",
                "url": "https://github.com/johndoe/tool",
                "inResume": True,
            }
        ],
        "personalSkills": {
            "Leadership": {
                "value": "Team Leadership",
                "inResume": True,
            }
        },
        "footer": {
            "value": "References available upon request",
            "inResume": False,
        },
    }


@pytest.fixture
def valid_schema() -> dict:
    """Load the actual resume schema for testing."""
    schema_path = (
        Path(__file__).parent.parent
        / "cv_builder"
        / "templates"
        / "resume"
        / "schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_template_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with template files."""
    template_dir = tmp_path / "templates" / "test_template"
    template_dir.mkdir(parents=True)

    # Create minimal template
    template_content = r"""<% for exp in cv.experience | resume_filter %>
<< exp.title | latex >> at << exp.company | latex >>
<< exp | date_range >>
<% for resp in exp | get_resp %>
- << resp | latex >>
<% endfor %>
<% endfor %>
"""
    (template_dir / "template.tex.j2").write_text(template_content, encoding="utf-8")

    # Create minimal .sty file
    (template_dir / "test_template.sty").write_text(
        "% Test style file\n", encoding="utf-8"
    )

    # Create minimal schema
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["personalInfo", "experience"],
        "additionalProperties": True,
        "properties": {
            "personalInfo": {"type": "object"},
            "experience": {"type": "array"},
        },
    }
    (template_dir / "schema.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )

    return template_dir


@pytest.fixture
def tmp_data_dir(tmp_path: Path, sample_cv_data: dict) -> Path:
    """Create a temporary data directory with sample data."""
    data_dir = tmp_path / "data" / "test_template"
    data_dir.mkdir(parents=True)

    (data_dir / "test_template.json").write_text(
        json.dumps(sample_cv_data, indent=2), encoding="utf-8"
    )

    return data_dir


@pytest.fixture
def mock_pdflatex(monkeypatch):
    """Mock subprocess.run for pdflatex calls."""
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "pdflatex output"
    mock_run.return_value.stderr = ""
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_pdflatex_failure(monkeypatch):
    """Mock subprocess.run for failed pdflatex calls."""
    mock_run = MagicMock()
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = "! LaTeX Error: File not found."
    mock_run.return_value.stderr = ""
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_pdflatex_not_found(monkeypatch):
    """Mock subprocess.run to simulate pdflatex not installed."""

    def raise_not_found(*args, **kwargs):
        raise FileNotFoundError("pdflatex not found")

    monkeypatch.setattr("subprocess.run", raise_not_found)
