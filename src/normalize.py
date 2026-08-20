import json
import re

from pathlib import Path
from typing import Iterable

from src.config import REFERENCE_DIR


# ---------------------------------------------------------
# Load reference data
# ---------------------------------------------------------

def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


ROLE_GROUPS = _load_json(
    REFERENCE_DIR / "roles.json"
)

SKILL_GROUPS = _load_json(
    REFERENCE_DIR / "skills.json"
)


# ---------------------------------------------------------
# Role patterns
#
# Order matters:
# more specific titles should appear before broad titles.
# ---------------------------------------------------------

ROLE_PATTERNS = [

    # -----------------------------------------------------
    # DATA & ANALYTICS
    # -----------------------------------------------------

    (
        "Business Intelligence Analyst",
        [
            r"\bbusiness intelligence analyst\b",
            r"\bbi analyst\b",
            r"\bbi reporting analyst\b",
        ],
    ),

    (
        "BI Developer",
        [
            r"\bbi developer\b",
            r"\bbusiness intelligence developer\b",
            r"\bpower bi developer\b",
        ],
    ),

    (
        "Financial Data Analyst",
        [
            r"\bfinancial data analyst\b",
            r"\bfinance data analyst\b",
        ],
    ),

    (
        "Risk Data Analyst",
        [
            r"\brisk data analyst\b",
            r"\brisk analytics analyst\b",
        ],
    ),

    (
        "Product Analyst",
        [
            r"\bproduct analyst\b",
            r"\bproduct analytics analyst\b",
        ],
    ),

    (
        "Data Analyst",
        [
            r"\bdata analyst\b",
            r"\binsight analyst\b",
            r"\binsights analyst\b",
            r"\bdata insights analyst\b",
            r"\breporting analyst\b",
        ],
    ),

    (
        "Business Analyst",
        [
            r"\bbusiness analyst\b",
            r"\bit business analyst\b",
            r"\btechnical business analyst\b",
        ],
    ),

    # -----------------------------------------------------
    # DATA SCIENCE & AI
    # -----------------------------------------------------

    (
        "Machine Learning Engineer",
        [
            r"\bmachine learning engineer\b",
            r"\bml engineer\b",
            r"\bmachine learning developer\b",
        ],
    ),

    (
        "AI Engineer",
        [
            r"\bai engineer\b",
            r"\bartificial intelligence engineer\b",
            r"\bgenerative ai engineer\b",
            r"\bgenai engineer\b",
        ],
    ),

    (
        "Data Scientist",
        [
            r"\bdata scientist\b",
            r"\bapplied data scientist\b",
        ],
    ),

    # -----------------------------------------------------
    # DATA ENGINEERING
    # -----------------------------------------------------

    (
        "Analytics Engineer",
        [
            r"\banalytics engineer\b",
        ],
    ),

    (
        "Cloud Data Engineer",
        [
            r"\bcloud data engineer\b",
        ],
    ),

    (
        "Data Engineer",
        [
            r"\bdata engineer\b",
            r"\bdata platform engineer\b",
            r"\bdata pipeline engineer\b",
        ],
    ),

    # -----------------------------------------------------
    # SOFTWARE DEVELOPMENT
    # -----------------------------------------------------

    (
        "Python Developer",
        [
            r"\bpython developer\b",
            r"\bpython software engineer\b",
            r"\bpython engineer\b",
        ],
    ),

    (
        "Web Developer",
        [
            r"\bweb developer\b",
            r"\bfront[- ]?end developer\b",
            r"\bfrontend developer\b",
            r"\bfull[- ]?stack developer\b",
            r"\bfullstack developer\b",
        ],
    ),

    (
        "Software Engineer",
        [
            r"\bsoftware engineer\b",
            r"\bsoftware developer\b",

            # Important additions
            r"\bsoftware development engineer\b",
            r"\bsoftware development developer\b",

            # SDET / test-development roles
            r"\bsoftware development engineer in test\b",
            r"\bsdet\b",

            # Variants
            r"\bapplication developer\b",
            r"\bapplication software engineer\b",
        ],
    ),

    # -----------------------------------------------------
    # CLOUD / DEVOPS
    # -----------------------------------------------------

    (
        "DevOps Engineer",
        [
            r"\bdevops engineer\b",
            r"\bdevops\b",
            r"\bsite reliability engineer\b",
            r"\bsre\b",
            r"\bplatform engineer\b",
        ],
    ),

    (
        "Cloud Engineer",
        [
            r"\bcloud engineer\b",
            r"\bcloud infrastructure engineer\b",
            r"\bcloud platform engineer\b",
            r"\bcloud infrastructure specialist\b",
        ],
    ),

    # -----------------------------------------------------
    # CYBER SECURITY
    # -----------------------------------------------------

    (
        "Cyber Security Analyst",
        [
            r"\bcyber ?security analyst\b",
            r"\bcybersecurity analyst\b",
            r"\bsecurity operations analyst\b",
            r"\bsoc analyst\b",
        ],
    ),

    (
        "Cyber Security Engineer",
        [
            r"\bcyber ?security engineer\b",
            r"\bcybersecurity engineer\b",
            r"\bsecurity engineer\b",
        ],
    ),

    (
        "Cyber Security",
        [
            r"\bcyber ?security lead\b",
            r"\bcybersecurity lead\b",
            r"\bcyber ?security consultant\b",
            r"\bcybersecurity consultant\b",
            r"\bcyber ?security auditor\b",
            r"\bsecurity auditor\b",
            r"\bcyber ?security specialist\b",
            r"\bcybersecurity specialist\b",
            r"\bcyber ?security manager\b",
            r"\binformation security consultant\b",
            r"\binformation security specialist\b",
        ],
    ),
]


# ---------------------------------------------------------
# Search-query fallbacks
#
# Converts collector queries into canonical roles.
# ---------------------------------------------------------

SEARCH_ROLE_ALIASES = {

    "Data Analyst":
        "Data Analyst",

    "Business Analyst":
        "Business Analyst",

    "Data Scientist":
        "Data Scientist",

    "Data Engineer":
        "Data Engineer",

    "Software Developer":
        "Software Engineer",

    "Cyber Security":
        "Cyber Security",

    "Cloud Engineer":
        "Cloud Engineer",

    "Web Developer":
        "Web Developer",
}


# ---------------------------------------------------------
# Explicit role-family mapping
#
# This prevents legitimate canonical roles being placed in
# Other / Unclassified simply because roles.json does not
# contain exactly the same label.
# ---------------------------------------------------------

ROLE_FAMILY_OVERRIDES = {

    # Data & Analytics
    "Data Analyst":
        "Data & Analytics",

    "Business Analyst":
        "Data & Analytics",

    "Business Intelligence Analyst":
        "Data & Analytics",

    "BI Developer":
        "Data & Analytics",

    "Product Analyst":
        "Data & Analytics",

    "Financial Data Analyst":
        "Data & Analytics",

    "Risk Data Analyst":
        "Data & Analytics",

    # Data Science & AI
    "Data Scientist":
        "Data Science & AI",

    "Machine Learning Engineer":
        "Data Science & AI",

    "AI Engineer":
        "Data Science & AI",

    # Data Engineering
    "Data Engineer":
        "Data Engineering",

    "Analytics Engineer":
        "Data Engineering",

    "Cloud Data Engineer":
        "Data Engineering",

    # Software
    "Software Engineer":
        "Software Development",

    "Software Developer":
        "Software Development",

    "Python Developer":
        "Software Development",

    "Web Developer":
        "Software Development",

    # Cloud
    "Cloud Engineer":
        "Cloud & Infrastructure",

    "DevOps Engineer":
        "Cloud & Infrastructure",

    # Cyber
    "Cyber Security":
        "Cybersecurity",

    "Cyber Security Analyst":
        "Cybersecurity",

    "Cyber Security Engineer":
        "Cybersecurity",
}


# ---------------------------------------------------------
# Role family
# ---------------------------------------------------------

def role_family_for(
    standard_role: str | None
) -> str:

    if not standard_role:
        return "Other / Unclassified"

    # First use explicit mapping
    if standard_role in ROLE_FAMILY_OVERRIDES:
        return ROLE_FAMILY_OVERRIDES[
            standard_role
        ]

    # Then preserve compatibility with roles.json
    cleaned_role = (
        standard_role
        .replace("Junior ", "")
        .replace("Senior ", "")
    )

    for family, roles in ROLE_GROUPS.items():

        if (
            standard_role in roles
            or cleaned_role in roles
        ):
            return family

    return "Other / Unclassified"


# ---------------------------------------------------------
# Seniority
# ---------------------------------------------------------

def classify_seniority(
    title: str | None,
    description: str | None = None,
) -> str:

    # Give the title greater conceptual importance.
    # Description is still useful because some adverts omit
    # seniority from the title.
    title_text = str(title or "")
    description_text = str(description or "")

    text = (
        f"{title_text} "
        f"{description_text}"
    ).lower()

    # Entry level
    if re.search(
        r"\b("
        r"intern|internship|graduate|"
        r"entry[- ]level|trainee|"
        r"apprentice|apprenticeship"
        r")\b",
        text,
    ):
        return "Entry / Graduate"

    # Junior
    if re.search(
        r"\b("
        r"junior|jr\.?|associate"
        r")\b",
        text,
    ):
        return "Junior"

    # Senior
    #
    # Check senior BEFORE generic manager terms where
    # appropriate, but high-level titles remain Lead/Manager.
    if re.search(
        r"\b("
        r"principal|staff|lead|"
        r"head of|director|manager"
        r")\b",
        title_text.lower(),
    ):
        return "Lead / Manager"

    if re.search(
        r"\b("
        r"senior|sr\.?"
        r")\b",
        title_text.lower(),
    ):
        return "Senior"

    # Description fallback
    if re.search(
        r"\b("
        r"principal|staff|lead|"
        r"head of|director"
        r")\b",
        description_text.lower(),
    ):
        return "Lead / Manager"

    if re.search(
        r"\b("
        r"senior|sr\.?"
        r")\b",
        description_text.lower(),
    ):
        return "Senior"

    return "Mid / Unspecified"


# ---------------------------------------------------------
# Standardise job title
# ---------------------------------------------------------

def standardize_role(
    title: str | None,
    search_role: str | None = None,
) -> str:

    title_text = (
        title or ""
    ).lower().strip()

    # First attempt:
    # classify using the actual job title.
    for role, patterns in ROLE_PATTERNS:

        if any(
            re.search(
                pattern,
                title_text,
            )
            for pattern in patterns
        ):
            return role

    # Second attempt:
    # use canonical search query mapping.
    if search_role:

        cleaned_search_role = (
            search_role
            .replace("Junior ", "")
            .replace("Senior ", "")
            .strip()
        )

        if (
            cleaned_search_role
            in SEARCH_ROLE_ALIASES
        ):
            return SEARCH_ROLE_ALIASES[
                cleaned_search_role
            ]

        return cleaned_search_role

    return "Other / Unclassified"


# ---------------------------------------------------------
# Skill matching
# ---------------------------------------------------------

def _phrase_pattern(
    alias: str
) -> re.Pattern:

    escaped = re.escape(
        alias.lower()
    )

    return re.compile(
        rf"(?<![a-z0-9])"
        rf"{escaped}"
        rf"(?![a-z0-9])",
        re.IGNORECASE,
    )


def extract_skills(
    text: str | None
) -> list[str]:

    if not text:
        return []

    found = []

    for category, skills in SKILL_GROUPS.items():

        for canonical, aliases in skills.items():

            if any(
                _phrase_pattern(alias).search(text)
                for alias in aliases
            ):
                found.append(
                    canonical
                )

    return sorted(
        set(found)
    )


def extract_skill_categories(
    skills: Iterable[str]
) -> list[str]:

    skill_set = set(
        skills
    )

    categories = []

    for category, mapping in SKILL_GROUPS.items():

        if any(
            skill in skill_set
            for skill in mapping
        ):
            categories.append(
                category
            )

    return sorted(
        categories
    )