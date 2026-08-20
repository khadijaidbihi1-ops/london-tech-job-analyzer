from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.config import PROCESSED_DIR


INPUT_FILE = PROCESSED_DIR / "jobs_processed.csv"
OUTPUT_DIR = PROCESSED_DIR.parent / "outputs"


def load_data() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "jobs_processed.csv not found. Run src.process_jobs first."
        )

    df = pd.read_csv(INPUT_FILE)

    df["salary_annual"] = pd.to_numeric(
        df.get("salary_annual"),
        errors="coerce",
    )

    return df


def save_chart(filename: str) -> None:
    path = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"Created: {path}")


def plot_job_demand(df: pd.DataFrame) -> None:
    counts = (
        df["standard_role"]
        .value_counts()
        .head(15)
        .sort_values()
    )

    plt.figure(figsize=(10, 7))
    counts.plot(kind="barh")

    plt.title("London Tech Job Demand by Role")
    plt.xlabel("Number of Job Adverts")
    plt.ylabel("Role")

    save_chart("job_demand_by_role.png")


def plot_salary_by_role(df: pd.DataFrame) -> None:
    salary_df = df[
        df["salary_annual"].notna()
        & (df["salary_annual"] >= 15000)
        & (df["salary_annual"] <= 250000)
    ].copy()

    summary = (
        salary_df
        .groupby("standard_role")
        .agg(
            median_salary=("salary_annual", "median"),
            jobs=("salary_annual", "size"),
        )
    )

    # Avoid drawing conclusions from roles represented
    # by only a handful of adverts.
    summary = summary[
        summary["jobs"] >= 10
    ]

    summary = (
        summary
        .sort_values("median_salary")
    )

    plt.figure(figsize=(10, 7))

    plt.barh(
        summary.index,
        summary["median_salary"],
    )

    plt.title("Median Annual Salary by Role")
    plt.xlabel("Median Annual Salary (£)")
    plt.ylabel("Role")

    save_chart("salary_by_role.png")


def plot_seniority(df: pd.DataFrame) -> None:
    order = [
        "Entry / Graduate",
        "Junior",
        "Mid / Unspecified",
        "Senior",
        "Lead / Manager",
    ]

    counts = (
        df["seniority"]
        .value_counts()
        .reindex(order)
        .fillna(0)
    )

    plt.figure(figsize=(10, 6))

    counts.plot(kind="bar")

    plt.title("Seniority Distribution")
    plt.xlabel("Seniority")
    plt.ylabel("Number of Job Adverts")
    plt.xticks(rotation=25, ha="right")

    save_chart("seniority_distribution.png")


def plot_entry_level(df: pd.DataFrame) -> None:
    entry = df[
        df["seniority"].isin(
            ["Entry / Graduate", "Junior"]
        )
    ]

    counts = (
        entry["standard_role"]
        .value_counts()
        .head(15)
        .sort_values()
    )

    plt.figure(figsize=(10, 7))

    counts.plot(kind="barh")

    plt.title("Entry-Level Opportunities by Role")
    plt.xlabel("Number of Entry / Junior Job Adverts")
    plt.ylabel("Role")

    save_chart("entry_level_by_role.png")


def plot_top_companies(df: pd.DataFrame) -> None:
    companies = (
        df["company"]
        .dropna()
        .value_counts()
        .head(15)
        .sort_values()
    )

    plt.figure(figsize=(10, 7))

    companies.plot(kind="barh")

    plt.title("Top Hiring Companies in the Dataset")
    plt.xlabel("Number of Job Adverts")
    plt.ylabel("Company")

    save_chart("top_hiring_companies.png")


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    print("=" * 60)
    print("LONDON TECH JOB ANALYZER - VISUALISATION")
    print("=" * 60)

    print(f"\nLoaded {len(df):,} processed job adverts.\n")

    plot_job_demand(df)
    plot_salary_by_role(df)
    plot_seniority(df)
    plot_entry_level(df)
    plot_top_companies(df)

    print("\n" + "=" * 60)
    print("VISUALISATION COMPLETE")
    print("=" * 60)

    print(
        f"\nCharts saved to:\n{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()