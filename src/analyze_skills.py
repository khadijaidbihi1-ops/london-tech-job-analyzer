from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR


INPUT_FILE = PROCESSED_DIR / "jobs_processed.csv"
OUTPUT_FILE = PROCESSED_DIR / "skills_analysis.csv"
ROLE_OUTPUT_FILE = PROCESSED_DIR / "skills_by_role.csv"


def load_jobs() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "jobs_processed.csv not found. Run src.process_jobs first."
        )

    df = pd.read_csv(INPUT_FILE)

    if "skills" not in df.columns:
        raise KeyError(
            "The processed dataset does not contain a 'skills' column."
        )

    return df


def explode_skills(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    working["skills"] = (
        working["skills"]
        .fillna("")
        .astype(str)
    )

    working["skill"] = (
        working["skills"]
        .str.split("|")
    )

    exploded = working.explode("skill")

    exploded["skill"] = (
        exploded["skill"]
        .fillna("")
        .str.strip()
    )

    exploded = exploded[
        exploded["skill"] != ""
    ].copy()

    return exploded


def build_overall_skill_analysis(
    df: pd.DataFrame,
    exploded: pd.DataFrame,
) -> pd.DataFrame:

    total_jobs = len(df)

    counts = (
        exploded
        .groupby("skill")["job_id"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index(name="job_adverts")
    )

    counts["share_of_jobs"] = (
        counts["job_adverts"]
        / total_jobs
        * 100
    )

    counts["share_of_jobs"] = (
        counts["share_of_jobs"]
        .round(2)
    )

    return counts


def build_skill_analysis_by_role(
    df: pd.DataFrame,
    exploded: pd.DataFrame,
) -> pd.DataFrame:

    role_totals = (
        df
        .groupby("standard_role")["job_id"]
        .nunique()
        .rename("role_job_count")
        .reset_index()
    )

    skill_counts = (
        exploded
        .groupby(
            [
                "standard_role",
                "skill",
            ]
        )["job_id"]
        .nunique()
        .reset_index(
            name="job_adverts"
        )
    )

    analysis = skill_counts.merge(
        role_totals,
        on="standard_role",
        how="left",
    )

    analysis["share_of_role_jobs"] = (
        analysis["job_adverts"]
        / analysis["role_job_count"]
        * 100
    )

    analysis["share_of_role_jobs"] = (
        analysis["share_of_role_jobs"]
        .round(2)
    )

    analysis = analysis.sort_values(
        [
            "standard_role",
            "job_adverts",
            "skill",
        ],
        ascending=[
            True,
            False,
            True,
        ],
    )

    return analysis


def print_summary(
    df: pd.DataFrame,
    overall: pd.DataFrame,
    by_role: pd.DataFrame,
) -> None:

    jobs_with_skills = (
        df["skills"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    print("=" * 70)
    print("LONDON TECH JOB ANALYZER - SKILLS INTELLIGENCE")
    print("=" * 70)

    print("\n1. COVERAGE")
    print("-" * 70)

    print(
        f"Total job adverts: {len(df):,}"
    )

    print(
        f"Jobs with >=1 detected skill: "
        f"{jobs_with_skills:,} "
        f"({jobs_with_skills / len(df):.1%})"
    )

    print(
        f"Jobs with no detected skills: "
        f"{len(df) - jobs_with_skills:,}"
    )

    print("\n2. TOP DETECTED SKILLS")
    print("-" * 70)

    if overall.empty:
        print("No skills detected.")
    else:
        print(
            overall
            .head(20)
            .to_string(
                index=False
            )
        )

    print("\n3. SAMPLE ROLE ANALYSIS")
    print("-" * 70)

    sample_roles = [
        "Data Analyst",
        "Software Engineer",
        "Data Engineer",
        "Web Developer",
        "Cloud Engineer",
        "Cyber Security",
    ]

    for role in sample_roles:

        role_data = by_role[
            by_role["standard_role"]
            == role
        ].head(10)

        if role_data.empty:
            continue

        print(f"\n{role}")

        print(
            role_data[
                [
                    "skill",
                    "job_adverts",
                    "share_of_role_jobs",
                ]
            ]
            .to_string(
                index=False
            )
        )

    print("\n" + "=" * 70)
    print("SKILLS ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"\nOverall analysis saved to:\n"
        f"{OUTPUT_FILE}"
    )

    print(
        f"\nRole analysis saved to:\n"
        f"{ROLE_OUTPUT_FILE}"
    )


def main() -> None:

    df = load_jobs()

    exploded = explode_skills(
        df
    )

    overall = build_overall_skill_analysis(
        df,
        exploded,
    )

    by_role = build_skill_analysis_by_role(
        df,
        exploded,
    )

    overall.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    by_role.to_csv(
        ROLE_OUTPUT_FILE,
        index=False,
    )

    print_summary(
        df,
        overall,
        by_role,
    )


if __name__ == "__main__":
    main()