"""Shared pytest fixtures for cv_builder tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_cv_data() -> dict:
    """Minimal valid CV data for testing."""
    return {
        "basics": {
            "name": "John Doe",
            "email": "john@example.com",
            "location": {"city": "New York", "region": "NY", "countryCode": "US"},
            "profiles": [
                {
                    "network": "LinkedIn",
                    "url": "https://linkedin.com/in/johndoe",
                    "x-inResume": True,
                },
                {
                    "network": "GitHub",
                    "url": "https://github.com/johndoe",
                    "x-inResume": True,
                },
            ],
        },
        "work": [
            {
                "position": "Software Engineer",
                "name": "Tech Corp",
                "location": "New York, NY",
                "startDate": "2020-01",
                "endDate": None,
                "summary": "Building software",
                "highlights": [
                    {"value": "Write code", "x-inResume": True},
                    {"value": "Review PRs", "x-inResume": False},
                ],
                "x-inResume": True,
            }
        ],
        "education": [
            {
                "area": "B.S. Computer Science",
                "institution": "State University",
                "location": "Boston, MA",
                "startDate": "2016-09",
                "endDate": "2020-05",
                "x-details": {},
                "x-inResume": True,
            }
        ],
        "certificates": [],
        "technicalSkills": {
            "Languages": {
                "value": "Python, JavaScript",
                "x-inResume": True,
            }
        },
        "projects": [
            {
                "name": "Open Source Tool",
                "description": "A CLI tool",
                "x-technologies": "Python",
                "url": "https://github.com/johndoe/tool",
                "x-inResume": True,
            }
        ],
        "personalSkills": {
            "Leadership": {
                "value": "Team Leadership",
                "x-inResume": True,
            }
        },
        "meta": {
            "footer": {
                "value": "References available upon request",
                "x-inResume": False,
            }
        },
    }


@pytest.fixture
def valid_schema() -> dict:
    """Load the actual resume schema for testing."""
    schema_path = (
        Path(__file__).parent.parent
        / "cv_builder"
        / "schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_template_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with template files."""
    template_dir = tmp_path / "templates" / "test_template"
    template_dir.mkdir(parents=True)

    # Create minimal template using new field names
    template_content = r"""<% for exp in cv.work | resume_filter %>
<< exp.position | latex >> at << exp.name | latex >>
<< exp | date_range >>
<% for h in exp | get_highlights %>
- << h | latex >>
<% endfor %>
<% endfor %>
"""
    (template_dir / "template.tex.j2").write_text(template_content, encoding="utf-8")

    # Create minimal .sty file
    (template_dir / "test_template.sty").write_text(
        "% Test style file\n", encoding="utf-8"
    )

    # Create minimal schema two levels above template dir (at tmp_path level),
    # matching production layout where cv_builder/schema.json sits above
    # cv_builder/templates/<name>/. In tests, get_package_templates_dir is
    # mocked to return tmp_path/templates, so schema_file = templates_dir.parent
    # / "schema.json" = tmp_path/schema.json.
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["basics", "work"],
        "additionalProperties": True,
        "properties": {
            "basics": {"type": "object"},
            "work": {"type": "array"},
        },
    }
    (template_dir.parent.parent / "schema.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )

    return template_dir


@pytest.fixture
def tmp_data_dir(tmp_path: Path, sample_cv_data: dict) -> Path:
    """Create a temporary data directory with sample data.

    Data lives at tmp_path/data/cv.json (flat, template-agnostic).
    Returns tmp_path/data so tests can reference data_dir / "cv.json".
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    (data_dir / "cv.json").write_text(
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
