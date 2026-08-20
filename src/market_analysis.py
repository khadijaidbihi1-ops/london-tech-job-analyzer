from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR


INPUT_FILE = PROCESSED_DIR / "jobs_processed.csv"
OUTPUT_FILE = PROCESSED_DIR / "market_analysis.csv"


def load_data() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "jobs_processed.csv not found. Run src.process_jobs first."
        )

    return pd.read_csv(INPUT_FILE)


def analyse_roles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a market summary for each standardised job role.
    """

    analysis = (
        df.groupby("standard_role")
        .agg(
            job_count=("job_id", "nunique"),
            company_count=("company", "nunique"),
            median_salary=("salary_annual", "median"),
            mean_salary=("salary_annual", "mean"),
            min_salary=("salary_annual", "min"),
            max_salary=("salary_annual", "max"),
        )   
        .reset_index()
    )

    analysis["market_share_pct"] = (
        analysis["job_count"] / analysis["job_count"].sum() * 100
    )

    analysis = analysis.sort_values(
        "job_count",
        ascending=False,
    )

    return analysis


def print_role_summary(analysis: pd.DataFrame) -> None:
    print("=" * 75)
    print("LONDON TECH JOB MARKET ANALYSIS")
    print("=" * 75)

    print("\n1. MARKET DEMAND")
    print("-" * 75)

    for _, row in analysis.head(15).iterrows():
        print(
            f"{row['standard_role']:<35}"
            f"{int(row['job_count']):>5} jobs  "
            f"{row['market_share_pct']:>6.1f}%"
        )

    print("\n2. MEDIAN SALARY BY ROLE")
    print("-" * 75)

    salary_view = analysis.sort_values(
        "median_salary",
        ascending=False,
    )

    for _, row in salary_view.head(15).iterrows():
        print(
            f"{row['standard_role']:<35}"
            f"£{row['median_salary']:>10,.0f}"
        )


def analyse_seniority(df: pd.DataFrame) -> None:
    print("\n3. SENIORITY DISTRIBUTION")
    print("-" * 75)

    seniority = df["seniority"].value_counts()

    for level, count in seniority.items():
        percentage = count / len(df) * 100

        print(
            f"{level:<25}"
            f"{count:>5} jobs  "
            f"{percentage:>6.1f}%"
        )


def analyse_entry_level(df: pd.DataFrame) -> None:
    print("\n4. ENTRY-LEVEL OPPORTUNITIES")
    print("-" * 75)

    entry_levels = [
        "Entry / Graduate",
        "Junior",
    ]

    entry_df = df[
        df["seniority"].isin(entry_levels)
    ]

    print(
        f"Entry/Junior jobs: {len(entry_df):,} "
        f"({len(entry_df) / len(df):.1%} of market)"
    )

    print("\nTop roles for entry-level candidates:")

    counts = (
        entry_df["standard_role"]
        .value_counts()
        .head(10)
    )

    for role, count in counts.items():
        print(f"{role:<35}{count:>5}")


def main() -> None:
    df = load_data()

    analysis = analyse_roles(df)

    analysis.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print_role_summary(analysis)
    analyse_seniority(df)
    analyse_entry_level(df)

    print("\n" + "=" * 75)
    print("ANALYSIS COMPLETE")
    print("=" * 75)

    print(
        f"\nAnalysed {len(df):,} London job adverts."
    )

    print(
        f"Role summary saved to:\n{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
    