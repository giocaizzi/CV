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
    format_location,
    format_month_year,
    get_highlights,
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
        invalid_data = {"basics": {"name": "John"}}
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
        item = {"startDate": "2020-01", "endDate": "2021-12"}
        assert env.filters["date_range"](item) == "Jan 2020 -- Dec 2021"

    def test_date_range_filter_with_none_end(self, tmp_template_dir: Path):
        """date_range filter handles None endDate."""
        env = create_jinja_env(tmp_template_dir)
        item = {"startDate": "2020-01", "endDate": None}
        assert env.filters["date_range"](item) == "Jan 2020"

    def test_resume_filter_registered(self, tmp_template_dir: Path):
        """resume_filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "resume_filter" in env.filters
        items = [{"x-inResume": True}, {"x-inResume": False}]
        assert len(env.filters["resume_filter"](items)) == 1

    def test_get_highlights_filter_registered(self, tmp_template_dir: Path):
        """get_highlights filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "get_highlights" in env.filters
        item = {"highlights": [{"value": "Task", "x-inResume": True}]}
        assert env.filters["get_highlights"](item) == ["Task"]

    def test_month_year_filter_registered(self, tmp_template_dir: Path):
        """month_year filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "month_year" in env.filters
        assert env.filters["month_year"]("2024-05") == "May 2024"

    def test_location_str_filter_registered(self, tmp_template_dir: Path):
        """location_str filter is registered and works."""
        env = create_jinja_env(tmp_template_dir)
        assert "location_str" in env.filters
        loc = {"city": "Milan", "countryCode": "IT"}
        assert env.filters["location_str"](loc) == "Milan, Italy"

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
        # Filtered out highlight should not appear
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


# =============================================================================
# format_month_year tests
# =============================================================================
@pytest.mark.unit
class TestFormatMonthYear:
    """Tests for format_month_year function."""

    def test_iso_month_year(self):
        """ISO YYYY-MM format converts to Mon YYYY."""
        assert format_month_year("2024-05") == "May 2024"

    def test_iso_july(self):
        assert format_month_year("2020-07") == "Jul 2020"

    def test_iso_january(self):
        assert format_month_year("2020-01") == "Jan 2020"

    def test_iso_december(self):
        assert format_month_year("2021-12") == "Dec 2021"

    def test_year_only(self):
        """Year-only string returns as-is."""
        assert format_month_year("2023") == "2023"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert format_month_year("") == ""

    def test_none(self):
        """None returns empty string."""
        assert format_month_year(None) == ""

    def test_no_periods_in_output(self):
        """Output month abbreviations have no trailing periods."""
        result = format_month_year("2021-02")
        assert "." not in result
        assert result == "Feb 2021"

    def test_all_months(self):
        """All 12 months map correctly."""
        expected = [
            ("2020-01", "Jan 2020"),
            ("2020-02", "Feb 2020"),
            ("2020-03", "Mar 2020"),
            ("2020-04", "Apr 2020"),
            ("2020-05", "May 2020"),
            ("2020-06", "Jun 2020"),
            ("2020-07", "Jul 2020"),
            ("2020-08", "Aug 2020"),
            ("2020-09", "Sep 2020"),
            ("2020-10", "Oct 2020"),
            ("2020-11", "Nov 2020"),
            ("2020-12", "Dec 2020"),
        ]
        for iso, display in expected:
            assert format_month_year(iso) == display

    def test_invalid_month_returns_original(self):
        """Invalid month index returns original string."""
        assert format_month_year("2020-13") == "2020-13"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        assert format_month_year("  2024-05  ") == "May 2024"

    def test_whitespace_only(self):
        """Whitespace-only input strips to empty and returns empty string."""
        assert format_month_year("   ") == ""


# =============================================================================
# format_location tests
# =============================================================================
@pytest.mark.unit
class TestFormatLocation:
    """Tests for format_location function."""

    def test_full_object(self):
        loc = {"city": "Milan", "region": "Lombardy", "countryCode": "IT"}
        assert format_location(loc) == "Milan, Lombardy, Italy"

    def test_city_and_country(self):
        assert format_location({"city": "Milan", "countryCode": "IT"}) == "Milan, Italy"

    def test_city_only(self):
        assert format_location({"city": "Milan"}) == "Milan"

    def test_country_only(self):
        assert format_location({"countryCode": "US"}) == "United States"

    def test_empty_object(self):
        assert format_location({}) == ""

    def test_unknown_country_code_passes_through(self):
        """Unknown ISO codes pass through unchanged (caller can extend COUNTRY_NAMES)."""
        assert format_location({"city": "X", "countryCode": "ZZ"}) == "X, ZZ"

    def test_none_returns_empty(self):
        assert format_location(None) == ""

    def test_plain_string_returned_as_is(self):
        """Backward compatibility: a plain string is returned unchanged."""
        assert format_location("Milan, Italy") == "Milan, Italy"

    def test_unexpected_type_returns_empty(self):
        """List or other non-supported type returns empty string."""
        assert format_location([1, 2, 3]) == ""
        assert format_location(42) == ""


# =============================================================================
# format_date_range tests
# =============================================================================
@pytest.mark.unit
class TestFormatDateRange:
    """Tests for format_date_range function."""

    def test_with_end_date(self):
        result = format_date_range("2020-01", "2021-12")
        assert result == "Jan 2020 -- Dec 2021"

    def test_with_none_end_date(self):
        """None end date returns just start (current/ongoing)."""
        assert format_date_range("2020-01", None) == "Jan 2020"

    def test_same_dates(self):
        result = format_date_range("2020-01", "2020-01")
        assert result == "Jan 2020 -- Jan 2020"

    def test_year_only_dates(self):
        result = format_date_range("2023", "2024")
        assert result == "2023 -- 2024"


# =============================================================================
# filter_by_resume tests
# =============================================================================
@pytest.mark.unit
class TestFilterByResume:
    """Tests for filter_by_resume function."""

    def test_filters_out_false(self):
        items = [
            {"name": "A", "x-inResume": True},
            {"name": "B", "x-inResume": False},
            {"name": "C", "x-inResume": True},
        ]
        result = filter_by_resume(items)
        assert len(result) == 2
        assert result[0]["name"] == "A"
        assert result[1]["name"] == "C"

    def test_defaults_to_true(self):
        """Items without x-inResume field default to included."""
        items = [{"name": "A"}, {"name": "B", "x-inResume": False}]
        result = filter_by_resume(items)
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_empty_list(self):
        assert filter_by_resume([]) == []


# =============================================================================
# get_highlights tests
# =============================================================================
@pytest.mark.unit
class TestGetHighlights:
    """Tests for get_highlights function."""

    def test_filters_highlights(self):
        item = {
            "highlights": [
                {"value": "Task A", "x-inResume": True},
                {"value": "Task B", "x-inResume": False},
                {"value": "Task C", "x-inResume": True},
            ]
        }
        result = get_highlights(item)
        assert result == ["Task A", "Task C"]

    def test_empty_highlights(self):
        assert get_highlights({}) == []
        assert get_highlights({"highlights": []}) == []

    def test_defaults_to_true(self):
        item = {
            "highlights": [
                {"value": "Task A"},
                {"value": "Task B", "x-inResume": False},
            ]
        }
        result = get_highlights(item)
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
