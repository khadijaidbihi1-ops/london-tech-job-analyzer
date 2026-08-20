import argparse
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR
from src.normalize import (
    classify_seniority,
    extract_skill_categories,
    extract_skills,
    role_family_for,
    standardize_role,
)


def latest_raw_file() -> Path:
    files = sorted(RAW_DIR.glob("adzuna_jobs_*.csv"))

    if not files:
        raise FileNotFoundError(
            "No raw job file found. Run src.collect_jobs first."
        )

    return files[-1]


def process_jobs(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    if df.empty:
        return df

    # -----------------------------------------------------
    # Basic type cleaning
    # -----------------------------------------------------

    df["created"] = pd.to_datetime(
        df["created"],
        errors="coerce",
        utc=True,
    )

    df["collected_at"] = pd.to_datetime(
        df["collected_at"],
        errors="coerce",
        utc=True,
    )

    df["salary_min"] = pd.to_numeric(
        df["salary_min"],
        errors="coerce",
    )

    df["salary_max"] = pd.to_numeric(
        df["salary_max"],
        errors="coerce",
    )

    df["salary_midpoint"] = df[
        ["salary_min", "salary_max"]
    ].mean(
        axis=1,
        skipna=False,
    )

    # -----------------------------------------------------
    # Salary validation
    # -----------------------------------------------------

    df["salary_midpoint_raw"] = df["salary_midpoint"]

    low_salary_mask = (
        df["salary_midpoint"].notna()
        & (df["salary_midpoint"] < 15000)
    )

    high_salary_mask = (
        df["salary_midpoint"].notna()
        & (df["salary_midpoint"] > 250000)
    )

    df["salary_quality_flag"] = "annual_salary"

    df.loc[
        low_salary_mask,
        "salary_quality_flag"
    ] = "ambiguous_pay_period"

    df.loc[
        high_salary_mask,
        "salary_quality_flag"
    ] = "high_annual_outlier"

    # Keep only salaries safe enough for annual analysis.
    # We do NOT invent annualised values for ambiguous
    # hourly / daily / monthly rates.
    df["salary_annual"] = df["salary_midpoint"].where(
        ~low_salary_mask
    )

    df["salary_valid_for_analysis"] = (
        df["salary_annual"].notna()
    )

    # -----------------------------------------------------
    # Support both old and new collector schemas
    # -----------------------------------------------------

    if "matched_search_roles" not in df.columns:
        if "search_role" in df.columns:
            df["matched_search_roles"] = df["search_role"]
        else:
            df["matched_search_roles"] = ""

    df["primary_search_role"] = (
        df["matched_search_roles"]
        .fillna("")
        .str.split(" | ", regex=False)
        .str[0]
    )

    # -----------------------------------------------------
    # Role normalisation
    # -----------------------------------------------------

    df["standard_role"] = [
        standardize_role(
            title,
            search_role,
        )
        for title, search_role in zip(
            df["raw_title"],
            df["primary_search_role"],
        )
    ]

    df["role_family"] = (
        df["standard_role"]
        .map(role_family_for)
    )

    # -----------------------------------------------------
    # Seniority
    # -----------------------------------------------------

    df["seniority"] = [
        classify_seniority(
            title,
            description,
        )
        for title, description in zip(
            df["raw_title"],
            df["description"],
        )
    ]

    # -----------------------------------------------------
    # Skill extraction
    #
    # Adzuna descriptions are usually truncated to
    # approximately 500 characters, so these fields are
    # exploratory only.
    # -----------------------------------------------------

    combined_text = (
        df["raw_title"].fillna("")
        + " "
        + df["description"].fillna("")
    )

    skill_lists = combined_text.map(
        extract_skills
    )

    df["skills"] = skill_lists.map(
        lambda values: "|".join(values)
    )

    df["skill_count"] = skill_lists.map(
        len
    )

    df["skill_categories"] = (
        skill_lists
        .map(extract_skill_categories)
        .map(
            lambda values: "|".join(values)
        )
    )

    # -----------------------------------------------------
    # Quality flags
    # -----------------------------------------------------

    df["has_salary"] = (
        df["salary_midpoint"].notna()
    )

    df["has_description"] = (
        df["description"]
        .fillna("")
        .str.len()
        .gt(30)
    )

    df["is_london"] = (
        df["location"]
        .fillna("")
        .str.contains(
            "London",
            case=False,
        )
        |
        df["location_area"]
        .fillna("")
        .str.contains(
            "London",
            case=False,
        )
    )

    if "description_length" not in df.columns:
        df["description_length"] = (
            df["description"]
            .fillna("")
            .str.len()
        )

    if "description_likely_truncated" not in df.columns:
        df["description_likely_truncated"] = (
            df["description_length"] >= 500
        )

    if "salary_available" not in df.columns:
        df["salary_available"] = (
            df["salary_min"].notna()
            | df["salary_max"].notna()
        )

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clean and enrich collected job adverts."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    input_path = (
        args.input
        or latest_raw_file()
    )

    print(
        f"Processing raw file:\n{input_path}"
    )

    df = process_jobs(
        input_path
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        PROCESSED_DIR
        / "jobs_processed.csv"
    )

    df.to_csv(
        output,
        index=False,
    )

    print(
        f"\nSaved {len(df):,} "
        f"processed jobs to:\n{output}"
    )

    if not df.empty:

        print("\nJobs by role family:")

        print(
            df["role_family"]
            .value_counts(dropna=False)
            .to_string()
        )

        print("\nStandard roles:")

        print(
            df["standard_role"]
            .value_counts(dropna=False)
            .to_string()
        )

        print("\nSeniority:")

        print(
            df["seniority"]
            .value_counts(dropna=False)
            .to_string()
        )

        print(
            "\nSalary coverage: "
            "{:.1%}".format(
                df["has_salary"].mean()
            )
        )

        print(
            "Salary valid for annual analysis: "
            "{:.1%}".format(
                df["salary_valid_for_analysis"].mean()
            )
        )

        print(
            "London coverage: "
            "{:.1%}".format(
                df["is_london"].mean()
            )
        )

        print(
            "Description truncation flag: "
            "{:.1%}".format(
                df[
                    "description_likely_truncated"
                ].mean()
            )
        )

        print("\nSalary quality flags:")

        print(
            df["salary_quality_flag"]
            .value_counts(dropna=False)
            .to_string()
        )


if __name__ == "__main__":
    main()