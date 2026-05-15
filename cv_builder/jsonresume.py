"""JSON Resume emitter for cv_builder.

Converts source cv_data (with x- extensions) into vanilla JSON Resume format
compatible with the JSON Resume ecosystem (https://jsonresume.org).
"""

import copy


def _strip_x_keys(obj):
    """Recursively remove all keys starting with 'x-' from dicts and lists.

    Works on a deep copy — caller is responsible for not mutating originals.
    """
    if isinstance(obj, dict):
        return {
            k: _strip_x_keys(v)
            for k, v in obj.items()
            if not k.startswith("x-")
        }
    if isinstance(obj, list):
        return [_strip_x_keys(item) for item in obj]
    return obj


def _convert_skills(skill_map: dict) -> list:
    """Convert an object-map of skills to a JSON Resume skills[] array.

    Input:  {"Languages": {"value": "Python, SQL", "x-inResume": true}, ...}
    Output: [{"name": "Languages", "keywords": ["Python", "SQL"]}, ...]

    Hidden categories (x-inResume: false) are dropped.
    """
    result = []
    for category_name, entry in skill_map.items():
        if not entry.get("x-inResume", True):
            continue
        raw_value = entry.get("value", "")
        keywords = [s.strip() for s in raw_value.split(",") if s.strip()]
        result.append({"name": category_name, "keywords": keywords})
    return result


def to_jsonresume(cv_data: dict) -> dict:
    """Convert source cv_data (with x- extensions) into vanilla JSON Resume.

    - Drops items where x-inResume is false (so the artifact represents the
      curated short version, matching what gets printed)
    - Strips all x-* keys recursively
    - Flattens work[*].highlights from [{value, x-inResume}] to [value, value]
    - Converts technicalSkills + personalSkills object-maps into a single
      skills[] array of {name, keywords[]} where keywords are comma-split
    - Drops meta.footer (no vanilla equivalent)
    - Drops nested work[*].x-projects entirely
    - Preserves all other fields as-is
    """
    data = copy.deepcopy(cv_data)

    # --- basics ---
    basics = data.get("basics", {})
    profiles_raw = basics.get("profiles", [])
    # Filter profiles by x-inResume, then strip x- keys
    basics["profiles"] = [
        _strip_x_keys(p)
        for p in profiles_raw
        if p.get("x-inResume", True)
    ]
    data["basics"] = _strip_x_keys(basics)

    # --- work ---
    work_raw = data.get("work", [])
    work_out = []
    for entry in work_raw:
        if not entry.get("x-inResume", True):
            continue
        # Flatten highlights: filter by x-inResume, map to plain strings
        highlights_raw = entry.get("highlights", [])
        entry["highlights"] = [
            h["value"]
            for h in highlights_raw
            if h.get("x-inResume", True)
        ]
        # Drop x-projects (top-level projects[] already covers projects)
        entry.pop("x-projects", None)
        # Vanilla JSON Resume omits endDate for ongoing positions (no null).
        if entry.get("endDate") is None:
            entry.pop("endDate", None)
        work_out.append(_strip_x_keys(entry))
    data["work"] = work_out

    # --- education ---
    education_raw = data.get("education", [])
    education_out = []
    for entry in education_raw:
        if not entry.get("x-inResume", True):
            continue
        # x-details has no vanilla equivalent — drop it (handled by _strip_x_keys)
        if entry.get("endDate") is None:
            entry.pop("endDate", None)
        education_out.append(_strip_x_keys(entry))
    data["education"] = education_out

    # --- certificates ---
    certs_raw = data.get("certificates", [])
    data["certificates"] = [
        _strip_x_keys(c)
        for c in certs_raw
        if c.get("x-inResume", True)
    ]

    # --- projects ---
    projects_raw = data.get("projects", [])
    data["projects"] = [
        _strip_x_keys(p)
        for p in projects_raw
        if p.get("x-inResume", True)
    ]

    # --- skills (technicalSkills + personalSkills → skills[]) ---
    technical = data.pop("technicalSkills", {})
    personal = data.pop("personalSkills", {})
    data["skills"] = _convert_skills(technical) + _convert_skills(personal)

    # --- meta ---
    meta = data.get("meta", {})
    if meta:
        # Drop footer (no vanilla equivalent)
        meta.pop("footer", None)
        if meta:
            data["meta"] = meta
        else:
            data.pop("meta", None)
    else:
        data.pop("meta", None)

    # Final pass: strip any remaining x-* keys at top level
    # (e.g. $schema or anything else we didn't handle explicitly)
    data = {k: v for k, v in data.items() if not k.startswith("x-")}
    # Also strip the $schema key (not part of vanilla JSON Resume output)
    data.pop("$schema", None)

    return data
