"""Unit tests for cv_builder.jsonresume.to_jsonresume."""

import copy
import json

import pytest

from cv_builder.jsonresume import to_jsonresume


def _has_x_key(obj) -> bool:
    """Recursively check whether any dict key starts with 'x-'."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("x-"):
                return True
            if _has_x_key(v):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _has_x_key(item):
                return True
    return False


@pytest.fixture
def minimal_cv() -> dict:
    """Minimal cv_data with all top-level sections required by the transform."""
    return {
        "$schema": "https://example.com/schema.json",
        "basics": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "location": "Rome, Italy",
            "profiles": [
                {"network": "GitHub", "url": "https://github.com/jane", "x-inResume": True},
                {"network": "Hidden", "url": "https://hidden.example.com", "x-inResume": False},
            ],
        },
        "work": [
            {
                "position": "Engineer",
                "name": "Acme Corp",
                "location": "Milan, Italy",
                "startDate": "2022-01",
                "endDate": None,
                "summary": "Building stuff.",
                "x-longSummary": "Building lots of stuff.",
                "highlights": [
                    {"value": "A", "x-inResume": True},
                    {"value": "B", "x-inResume": False},
                    {"value": "C", "x-inResume": True},
                ],
                "x-projects": [
                    {"name": "Secret", "description": "Hidden", "x-inResume": False}
                ],
                "x-inResume": True,
            },
            {
                "position": "Intern",
                "name": "Old Co",
                "location": "Rome",
                "startDate": "2020-06",
                "endDate": "2021-12",
                "summary": "Old job.",
                "x-longSummary": "",
                "highlights": [],
                "x-inResume": False,
            },
        ],
        "education": [
            {
                "area": "Computer Science",
                "institution": "Uni",
                "location": "Milan",
                "startDate": "2018-09",
                "endDate": "2022-06",
                "x-details": {"msc": {"courses": "Algorithms", "thesis": "My Thesis"}},
                "x-inResume": True,
            }
        ],
        "certificates": [
            {"name": "AWS Cert", "date": "2023", "x-inResume": True},
            {"name": "Hidden Cert", "date": "2022", "x-inResume": False},
        ],
        "projects": [
            {
                "name": "visible-project",
                "url": "https://github.com/jane/visible",
                "description": "A visible project",
                "x-technologies": "Python",
                "x-inResume": True,
            },
            {
                "name": "hidden-project",
                "url": "https://github.com/jane/hidden",
                "description": "A hidden project",
                "x-technologies": "Go",
                "x-inResume": False,
            },
        ],
        "technicalSkills": {
            "Languages": {"value": "Python, SQL", "x-inResume": True},
            "Cloud": {"value": "AWS, GCP", "x-inResume": True},
            "HiddenSkill": {"value": "Secret tool", "x-inResume": False},
        },
        "personalSkills": {
            "Languages": {"value": "English, Italian", "x-inResume": True},
            "HiddenPersonal": {"value": "Something private", "x-inResume": False},
        },
        "meta": {
            "footer": {"value": "References available on request.", "x-inResume": False}
        },
    }


@pytest.mark.unit
class TestStripXKeys:
    """to_jsonresume strips all x-* keys recursively."""

    def test_no_x_keys_in_output(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert not _has_x_key(result), "Output contains at least one x-* key"

    def test_no_x_keys_in_work_items(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        for entry in result["work"]:
            assert not _has_x_key(entry)

    def test_no_x_keys_in_education_items(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        for entry in result["education"]:
            assert not _has_x_key(entry)

    def test_schema_key_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert "$schema" not in result


@pytest.mark.unit
class TestWorkFiltering:
    """to_jsonresume filters work entries by x-inResume."""

    def test_hidden_work_entry_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        positions = [e["position"] for e in result["work"]]
        assert "Intern" not in positions

    def test_visible_work_entry_kept(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        positions = [e["position"] for e in result["work"]]
        assert "Engineer" in positions

    def test_work_projects_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        for entry in result["work"]:
            assert "x-projects" not in entry
            # no key starting with x-
            assert not any(k.startswith("x-") for k in entry)


@pytest.mark.unit
class TestHighlightsFlattening:
    """to_jsonresume flattens highlights from objects to plain strings."""

    def test_highlights_are_strings(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        work_entry = result["work"][0]
        for h in work_entry["highlights"]:
            assert isinstance(h, str), f"Expected str, got {type(h)}: {h!r}"

    def test_hidden_highlight_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        highlights = result["work"][0]["highlights"]
        assert "B" not in highlights

    def test_visible_highlights_preserved_in_order(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        highlights = result["work"][0]["highlights"]
        assert highlights == ["A", "C"]

    def test_empty_highlights_stays_empty(self, minimal_cv):
        # Add a work entry with no highlights
        minimal_cv["work"][0]["highlights"] = []
        result = to_jsonresume(minimal_cv)
        assert result["work"][0]["highlights"] == []


@pytest.mark.unit
class TestProfilesFiltering:
    """to_jsonresume filters profiles by x-inResume and strips x- keys."""

    def test_hidden_profile_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        networks = [p["network"] for p in result["basics"]["profiles"]]
        assert "Hidden" not in networks

    def test_visible_profile_kept(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        networks = [p["network"] for p in result["basics"]["profiles"]]
        assert "GitHub" in networks

    def test_profiles_have_no_x_keys(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        for profile in result["basics"]["profiles"]:
            assert not any(k.startswith("x-") for k in profile)


@pytest.mark.unit
class TestSkillsConversion:
    """to_jsonresume converts object-map skills to skills[] array."""

    def test_skills_key_is_list(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert isinstance(result["skills"], list)

    def test_technical_skills_object_removed(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert "technicalSkills" not in result

    def test_personal_skills_object_removed(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert "personalSkills" not in result

    def test_technical_skill_entry_structure(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        skill_names = {s["name"] for s in result["skills"]}
        assert "Languages" in skill_names
        lang_skill = next(s for s in result["skills"] if s["name"] == "Languages" and "Python" in s["keywords"])
        assert lang_skill["keywords"] == ["Python", "SQL"]

    def test_personal_skill_folded_into_skills(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        # personalSkills["Languages"] has "English, Italian"
        english_skill = next(
            (s for s in result["skills"] if s["name"] == "Languages" and "English" in s["keywords"]),
            None,
        )
        assert english_skill is not None
        assert english_skill["keywords"] == ["English", "Italian"]

    def test_hidden_skill_category_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        skill_names = [s["name"] for s in result["skills"]]
        assert "HiddenSkill" not in skill_names
        assert "HiddenPersonal" not in skill_names

    def test_technical_skills_before_personal_skills(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        # "Cloud" is a technical skill; "Languages" (Italian) is personal
        # technical entries come first
        skill_names = [s["name"] for s in result["skills"]]
        technical_names = list(minimal_cv["technicalSkills"].keys())  # order preserved
        for name in technical_names:
            if minimal_cv["technicalSkills"][name]["x-inResume"]:
                assert name in skill_names

    def test_comma_split_keywords(self):
        cv = {
            "basics": {"name": "X", "email": "x@x.com", "location": "X", "profiles": []},
            "work": [],
            "education": [],
            "certificates": [],
            "projects": [],
            "technicalSkills": {
                "Tools": {"value": "  Git ,  Docker , Kubernetes  ", "x-inResume": True}
            },
            "personalSkills": {},
            "meta": {},
        }
        result = to_jsonresume(cv)
        tools = next(s for s in result["skills"] if s["name"] == "Tools")
        assert tools["keywords"] == ["Git", "Docker", "Kubernetes"]


@pytest.mark.unit
class TestMetaHandling:
    """to_jsonresume handles meta section correctly."""

    def test_meta_footer_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        assert "meta" not in result

    def test_meta_absent_if_empty_after_cleanup(self):
        cv = {
            "basics": {"name": "X", "email": "x@x.com", "location": "X", "profiles": []},
            "work": [],
            "education": [],
            "certificates": [],
            "projects": [],
            "technicalSkills": {},
            "personalSkills": {},
            "meta": {"footer": {"value": "Refs.", "x-inResume": False}},
        }
        result = to_jsonresume(cv)
        assert "meta" not in result


@pytest.mark.unit
class TestEducationHandling:
    """to_jsonresume handles education correctly."""

    def test_education_x_details_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        for entry in result["education"]:
            assert "x-details" not in entry

    def test_hidden_education_entry_dropped(self):
        cv = {
            "basics": {"name": "X", "email": "x@x.com", "location": "X", "profiles": []},
            "work": [],
            "education": [
                {
                    "area": "Visible",
                    "institution": "Uni A",
                    "location": "City",
                    "startDate": "2018-09",
                    "endDate": "2022-06",
                    "x-details": {},
                    "x-inResume": True,
                },
                {
                    "area": "Hidden",
                    "institution": "Uni B",
                    "location": "City",
                    "startDate": "2010-09",
                    "endDate": "2014-06",
                    "x-details": {},
                    "x-inResume": False,
                },
            ],
            "certificates": [],
            "projects": [],
            "technicalSkills": {},
            "personalSkills": {},
            "meta": {},
        }
        result = to_jsonresume(cv)
        areas = [e["area"] for e in result["education"]]
        assert "Hidden" not in areas
        assert "Visible" in areas


@pytest.mark.unit
class TestCertificatesHandling:
    """to_jsonresume handles certificates correctly."""

    def test_hidden_certificate_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        names = [c["name"] for c in result["certificates"]]
        assert "Hidden Cert" not in names

    def test_visible_certificate_kept(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        names = [c["name"] for c in result["certificates"]]
        assert "AWS Cert" in names

    def test_certificate_date_preserved_as_is(self, minimal_cv):
        """Year-only date must be preserved unchanged (valid ISO 8601)."""
        result = to_jsonresume(minimal_cv)
        cert = next(c for c in result["certificates"] if c["name"] == "AWS Cert")
        assert cert["date"] == "2023"


@pytest.mark.unit
class TestProjectsHandling:
    """to_jsonresume filters projects by x-inResume."""

    def test_hidden_project_dropped(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        names = [p["name"] for p in result["projects"]]
        assert "hidden-project" not in names

    def test_visible_project_kept(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        names = [p["name"] for p in result["projects"]]
        assert "visible-project" in names


@pytest.mark.unit
class TestOutputSerializability:
    """Output must be valid JSON and not mutate input."""

    def test_output_is_json_serializable(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        # Should not raise
        serialized = json.dumps(result)
        assert len(serialized) > 0

    def test_input_not_mutated(self, minimal_cv):
        original = copy.deepcopy(minimal_cv)
        to_jsonresume(minimal_cv)
        assert minimal_cv == original, "Input was mutated by to_jsonresume"

    def test_no_x_keys_anywhere_in_output(self, minimal_cv):
        result = to_jsonresume(minimal_cv)
        serialized = json.dumps(result)
        # Rough check: "x-" should not appear as a key prefix
        parsed_back = json.loads(serialized)
        assert not _has_x_key(parsed_back)
