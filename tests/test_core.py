"""Tests for cv_builder.core module."""

import json
from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

from cv_builder.core import (
    build_variant,
    compile_pdf,
    create_jinja_env,
    filter_by_resume,
    format_date_range,
    get_responsibilities,
    latex_escape,
    load_json,
    validate_cv,
)


# =============================================================================
# load_json tests
# =============================================================================
@pytest.mark.unit
class TestLoadJson:
    """Tests for load_json function."""

    def test_loads_valid_json(self, tmp_path: Path):
        """Valid JSON file is loaded correctly."""
        data = {"key": "value", "nested": {"a": 1}}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = load_json(json_file)
        assert result == data

    def test_file_not_found_raises(self, tmp_path: Path):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path: Path):
        """Malformed JSON raises JSONDecodeError."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_json(json_file)

    def test_empty_file_raises(self, tmp_path: Path):
        """Empty file raises JSONDecodeError."""
        json_file = tmp_path / "empty.json"
        json_file.write_text("", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_json(json_file)

    def test_utf8_encoding(self, tmp_path: Path):
        """UTF-8 characters are handled correctly."""
        data = {"name": "José García", "city": "München"}
        json_file = tmp_path / "utf8.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = load_json(json_file)
        assert result["name"] == "José García"
        assert result["city"] == "München"


# =============================================================================
# validate_cv tests
# =============================================================================
@pytest.mark.unit
class TestValidateCv:
    """Tests for validate_cv function."""

    def test_valid_data_returns_true(self, sample_cv_data, valid_schema, capsys):
        """Valid CV data passes validation."""
        result = validate_cv(sample_cv_data, valid_schema)
        assert result is True
        captured = capsys.readouterr()
        assert "✓" in captured.out

    def test_missing_required_field_returns_false(self, valid_schema, capsys):
        """Missing required field fails validation."""
        invalid_data = {"personalInfo": {"name": "John"}}
        result = validate_cv(invalid_data, valid_schema)
        assert result is False
        captured = capsys.readouterr()
        assert "✗" in captured.out

    def test_additional_properties_rejected(self, capsys):
        """Extra properties are rejected when additionalProperties=false."""
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"name": {"type": "string"}},
        }
        data = {"name": "John", "extra": "field"}
        result = validate_cv(data, schema)
        assert result is False
        captured = capsys.readouterr()
        assert "✗" in captured.out

    def test_type_mismatch_returns_false(self, capsys):
        """Wrong type fails validation."""
        schema = {"type": "object", "properties": {"age": {"type": "integer"}}}
        data = {"age": "not a number"}
        result = validate_cv(data, schema)
        assert result is False

    def test_prints_path_on_error(self, capsys):
        """Error message includes path to invalid field."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {"age": {"type": "integer"}},
                }
            },
        }
        data = {"person": {"age": "invalid"}}
        validate_cv(data, schema)
        captured = capsys.readouterr()
        assert "Path:" in captured.out


# =============================================================================
# create_jinja_env tests
# =============================================================================
@pytest.mark.unit
class TestCreateJinjaEnv:
    """Tests for create_jinja_env function."""

    def test_custom_delimiters(self, tmp_template_dir: Path):
        """Custom delimiters are configured correctly."""
        env = create_jinja_env(tmp_template_dir)
        assert env.block_start_string == "<%"
        assert env.block_end_string == "%>"
        assert env.variable_start_string == "<<"
        assert env.variable_end_string == ">>"
        assert env.comment_start_string == "<#"
        assert env.comment_end_string == "#>"

    def test_latex_filter_registered(self, tmp_template_dir: Path):
        """latex filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "latex" in env.filters
        assert env.filters["latex"]("&") == r"\&"

    def test_date_range_filter_registered(self, tmp_template_dir: Path):
        """date_range filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "date_range" in env.filters
        item = {"startDate": "Jan 2020", "endDate": "Dec 2021"}
        assert env.filters["date_range"](item) == "Jan 2020 -- Dec 2021"

    def test_date_range_filter_with_none_end(self, tmp_template_dir: Path):
        """date_range filter handles None endDate."""
        env = create_jinja_env(tmp_template_dir)
        item = {"startDate": "Jan 2020", "endDate": None}
        assert env.filters["date_range"](item) == "Jan 2020"

    def test_resume_filter_registered(self, tmp_template_dir: Path):
        """resume_filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "resume_filter" in env.filters
        items = [{"inResume": True}, {"inResume": False}]
        assert len(env.filters["resume_filter"](items)) == 1

    def test_get_resp_filter_registered(self, tmp_template_dir: Path):
        """get_resp filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "get_resp" in env.filters
        item = {"responsibilities": [{"value": "Task", "inResume": True}]}
        assert env.filters["get_resp"](item) == ["Task"]

    def test_autoescape_disabled(self, tmp_template_dir: Path):
        """Autoescape is disabled for LaTeX output."""
        env = create_jinja_env(tmp_template_dir)
        assert env.autoescape is False


# =============================================================================
# build_variant tests
# =============================================================================
@pytest.mark.unit
class TestBuildVariant:
    """Tests for build_variant function."""

    def test_generates_tex_file(
        self, tmp_template_dir: Path, tmp_path: Path, sample_cv_data
    ):
        """build_variant generates .tex file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = build_variant(
            tmp_template_dir, output_dir, "test_template", sample_cv_data
        )

        assert result.exists()
        assert result.suffix == ".tex"
        assert result.name == "test_template.tex"

    def test_output_contains_rendered_data(
        self, tmp_template_dir: Path, tmp_path: Path, sample_cv_data
    ):
        """Generated .tex file contains rendered CV data."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = build_variant(
            tmp_template_dir, output_dir, "test_template", sample_cv_data
        )
        content = result.read_text()

        assert "Software Engineer" in content
        assert "Tech Corp" in content
        assert "Write code" in content
        # Filtered out responsibility should not appear
        assert "Review PRs" not in content

    def test_template_not_found_raises(self, tmp_path: Path, sample_cv_data):
        """Missing template raises TemplateNotFound."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(TemplateNotFound):
            build_variant(empty_dir, tmp_path, "test", sample_cv_data)

    def test_prints_success_message(
        self, tmp_template_dir: Path, tmp_path: Path, sample_cv_data, capsys
    ):
        """Success message is printed."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        build_variant(tmp_template_dir, output_dir, "test_template", sample_cv_data)
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "Generated" in captured.out


# =============================================================================
# compile_pdf tests
# =============================================================================
@pytest.mark.unit
class TestCompilePdf:
    """Tests for compile_pdf function."""

    def test_successful_compilation(
        self, tmp_template_dir: Path, tmp_path: Path, mock_pdflatex
    ):
        """Successful pdflatex returns True."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"\documentclass{article}\begin{document}Hi\end{document}")

        result = compile_pdf(tex_file, tmp_template_dir)

        assert result is True
        mock_pdflatex.assert_called_once()

    def test_copies_sty_file(
        self, tmp_template_dir: Path, tmp_path: Path, mock_pdflatex
    ):
        """Style file is copied to output directory."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"\documentclass{article}")

        compile_pdf(tex_file, tmp_template_dir)

        sty_file = tmp_path / "test_template.sty"
        assert sty_file.exists()

    def test_compilation_failure_returns_false(
        self, tmp_template_dir: Path, tmp_path: Path, mock_pdflatex_failure, capsys
    ):
        """Failed pdflatex returns False."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"\documentclass{article}")

        result = compile_pdf(tex_file, tmp_template_dir)

        assert result is False
        captured = capsys.readouterr()
        assert "✗" in captured.out

    def test_pdflatex_not_found_returns_false(
        self, tmp_template_dir: Path, tmp_path: Path, mock_pdflatex_not_found, capsys
    ):
        """Missing pdflatex returns False with message."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"\documentclass{article}")

        result = compile_pdf(tex_file, tmp_template_dir)

        assert result is False
        captured = capsys.readouterr()
        assert "pdflatex not found" in captured.out


# =============================================================================
# latex_escape tests
# =============================================================================
@pytest.mark.unit
class TestLatexEscape:
    """Tests for latex_escape function."""

    def test_escapes_ampersand(self):
        assert latex_escape("Python & SQL") == r"Python \& SQL"

    def test_escapes_percent(self):
        assert latex_escape("100% complete") == r"100\% complete"

    def test_escapes_dollar(self):
        assert latex_escape("$100") == r"\$100"

    def test_escapes_hash(self):
        assert latex_escape("item #1") == r"item \#1"

    def test_escapes_underscore(self):
        assert latex_escape("my_var") == r"my\_var"

    def test_escapes_braces(self):
        assert latex_escape("{text}") == r"\{text\}"

    def test_escapes_tilde(self):
        assert latex_escape("~test") == r"\textasciitilde{}test"

    def test_escapes_caret(self):
        assert latex_escape("x^2") == r"x\textasciicircum{}2"

    def test_no_escape_needed(self):
        assert latex_escape("Hello World") == "Hello World"

    def test_non_string_returns_unchanged(self):
        assert latex_escape(123) == 123
        assert latex_escape(None) is None

    def test_multiple_special_chars(self):
        assert latex_escape("A & B % C") == r"A \& B \% C"


@pytest.mark.unit
class TestLatexEscapeRawLatex:
    """Tests for /latex{} raw LaTeX passthrough syntax."""

    def test_raw_latex_simple_ampersand(self):
        """Raw LaTeX content preserves backslash commands."""
        # /latex{\&} outputs \& which LaTeX renders as &
        result = latex_escape(r"/latex{\&}")
        assert result == r"\&"

    def test_raw_latex_with_surrounding_text(self):
        """Raw LaTeX preserves content while escaping surrounding text."""
        result = latex_escape(r"Python /latex{\&} SQL")
        assert result == r"Python \& SQL"

    def test_raw_latex_textbf(self):
        """Raw LaTeX with nested braces works."""
        result = latex_escape(r"Use /latex{\textbf{bold}} text")
        assert result == r"Use \textbf{bold} text"

    def test_raw_latex_textit(self):
        """Raw LaTeX with italic command."""
        result = latex_escape(r"Use /latex{\textit{italic}} here")
        assert result == r"Use \textit{italic} here"

    def test_raw_latex_href(self):
        """Raw LaTeX with href containing nested braces."""
        result = latex_escape(r"/latex{\href{http://example.com}{link}}")
        assert result == r"\href{http://example.com}{link}"

    def test_raw_latex_mixed_with_escape(self):
        """Mix of raw LaTeX and text needing escape."""
        result = latex_escape(r"Mixed /latex{\textit{italic}} and 100%")
        assert result == r"Mixed \textit{italic} and 100\%"

    def test_multiple_raw_latex_sections(self):
        """Multiple /latex{} sections in same string."""
        inp = r"A /latex{\textbf{b}} and /latex{\textit{c}} end"
        result = latex_escape(inp)
        assert result == r"A \textbf{b} and \textit{c} end"

    def test_raw_latex_empty(self):
        """Empty /latex{} is valid."""
        result = latex_escape(r"before /latex{} after")
        assert result == "before  after"

    def test_raw_latex_backslash_only(self):
        """Raw LaTeX with just backslash commands."""
        result = latex_escape(r"/latex{\LaTeX}")
        assert result == r"\LaTeX"


@pytest.mark.unit
class TestFormatDateRange:
    """Tests for format_date_range function."""

    def test_with_end_date(self):
        result = format_date_range("Jan 2020", "Dec 2021")
        assert result == "Jan 2020 -- Dec 2021"

    def test_with_none_end_date(self):
        """None end date returns just start (current/ongoing)."""
        assert format_date_range("Jan 2020", None) == "Jan 2020"

    def test_same_dates(self):
        result = format_date_range("Jan 2020", "Jan 2020")
        assert result == "Jan 2020 -- Jan 2020"


@pytest.mark.unit
class TestFilterByResume:
    """Tests for filter_by_resume function."""

    def test_filters_out_false(self):
        items = [
            {"name": "A", "inResume": True},
            {"name": "B", "inResume": False},
            {"name": "C", "inResume": True},
        ]
        result = filter_by_resume(items)
        assert len(result) == 2
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"

    def test_defaults_to_true(self):
        """Items without inResume field default to included."""
        items = [{"name": "A"}, {"name": "B", "inResume": False}]
        result = filter_by_resume(items)
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_empty_list(self):
        assert filter_by_resume([]) == []


@pytest.mark.unit
class TestGetResponsibilities:
    """Tests for get_responsibilities function."""

    def test_filters_responsibilities(self):
        item = {
            "responsibilities": [
                {"value": "Task A", "inResume": True},
                {"value": "Task B", "inResume": False},
                {"value": "Task C", "inResume": True},
            ]
        }
        result = get_responsibilities(item)
        assert result == ["Task A", "Task C"]

    def test_empty_responsibilities(self):
        assert get_responsibilities({}) == []
        assert get_responsibilities({"responsibilities": []}) == []

    def test_defaults_to_true(self):
        item = {
            "responsibilities": [
                {"value": "Task A"},
                {"value": "Task B", "inResume": False},
            ]
        }
        result = get_responsibilities(item)
        assert result == ["Task A"]


@pytest.mark.unit
class TestLatexEscapeEdgeCases:
    """Edge case tests for latex_escape."""

    def test_empty_string(self):
        assert latex_escape("") == ""

    def test_only_special_chars(self):
        assert latex_escape("&%$#_{}~^") == (
            r"\&\%\$\#\_\{\}"
            r"\textasciitilde{}\textasciicircum{}"
        )

    def test_raw_latex_not_matched_without_braces(self):
        """Text like /latex without braces is not processed."""
        result = latex_escape("/latex test")
        assert result == "/latex test"

    def test_raw_latex_incomplete(self):
        """Incomplete /latex{ syntax is not processed."""
        result = latex_escape("/latex{incomplete")
        assert result == r"/latex\{incomplete"

    def test_nested_braces_two_levels(self):
        """Raw LaTeX with two levels of nested braces."""
        result = latex_escape(r"/latex{\cmd{a}{b}}")
        assert result == r"\cmd{a}{b}"

    def test_backslash_in_normal_text(self):
        """Backslash in normal text is preserved (not a special char)."""
        result = latex_escape(r"path\to\file")
        assert result == r"path\to\file"

    def test_adjacent_raw_latex(self):
        """Adjacent /latex{} sections work correctly."""
        result = latex_escape(r"/latex{\a}/latex{\b}")
        assert result == r"\a\b"

    def test_real_world_skill_example(self):
        """Real-world example from skills section."""
        inp = r"Python, SQL /latex{\&} NoSQL, Docker"
        result = latex_escape(inp)
        assert result == r"Python, SQL \& NoSQL, Docker"

    def test_list_input(self):
        """Non-string inputs return unchanged."""
        assert latex_escape(["a", "b"]) == ["a", "b"]
        assert latex_escape({"key": "val"}) == {"key": "val"}
