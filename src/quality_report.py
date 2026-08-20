import pandas as pd

from src.config import PROCESSED_DIR


def main():
    path = PROCESSED_DIR / "jobs_processed.csv"

    if not path.exists():
        raise FileNotFoundError(
            "jobs_processed.csv not found. Run src.process_jobs first."
        )

    df = pd.read_csv(path)

    print("=" * 65)
    print("LONDON TECH JOB ANALYZER - DATA QUALITY REPORT")
    print("=" * 65)

    # ---------------------------------------------------------
    # 1. DATASET OVERVIEW
    # ---------------------------------------------------------
    print("\n1. DATASET OVERVIEW")
    print("-" * 65)

    print(f"Rows: {len(df):,}")

    if "job_id" in df.columns:
        unique_ids = df["job_id"].nunique()
        duplicate_ids = df["job_id"].duplicated().sum()

        print(f"Unique job IDs: {unique_ids:,}")
        print(f"Duplicate job IDs: {duplicate_ids:,}")

    print(f"Columns: {len(df.columns)}")

    # ---------------------------------------------------------
    # 2. COVERAGE
    # ---------------------------------------------------------
    print("\n2. DATA COVERAGE")
    print("-" * 65)

    if "is_london" in df.columns:
        print(f"London coverage: {df['is_london'].mean():.1%}")

    if "has_description" in df.columns:
        print(
            f"Description coverage: "
            f"{df['has_description'].mean():.1%}"
        )

    if "has_salary" in df.columns:
        print(f"Salary coverage: {df['has_salary'].mean():.1%}")

    if "skill_count" in df.columns:
        skill_coverage = (df["skill_count"] > 0).mean()
        print(f"Jobs with >=1 detected skill: {skill_coverage:.1%}")

    # ---------------------------------------------------------
    # 3. MISSING VALUES
    # ---------------------------------------------------------
    print("\n3. MISSING VALUES")
    print("-" * 65)

    important_columns = [
        "job_id",
        "raw_title",
        "company",
        "location",
        "description",
        "salary_min",
        "salary_max",
        "standard_role",
        "role_family",
        "seniority",
        "skills",
    ]

    for column in important_columns:
        if column in df.columns:
            missing = df[column].isna().sum()
            percentage = df[column].isna().mean()

            print(
                f"{column:<22} "
                f"{missing:>6,} "
                f"({percentage:>6.1%})"
            )

    # ---------------------------------------------------------
    # 4. SALARY QUALITY
    # ---------------------------------------------------------
    print("\n4. SALARY QUALITY")
    print("-" * 65)

    if "salary_midpoint" in df.columns:

        salary = pd.to_numeric(
            df["salary_midpoint"],
            errors="coerce"
        )

        valid_salary = salary.dropna()

        if not valid_salary.empty:

            print(f"Minimum: £{valid_salary.min():,.0f}")
            print(f"Median:  £{valid_salary.median():,.0f}")
            print(f"Mean:    £{valid_salary.mean():,.0f}")
            print(f"Maximum: £{valid_salary.max():,.0f}")

            low_salary = (valid_salary < 15000).sum()
            high_salary = (valid_salary > 250000).sum()

            print(
                f"Potentially low salaries (<£15k): "
                f"{low_salary:,}"
            )

            print(
                f"Potentially high salaries (>£250k): "
                f"{high_salary:,}"
            )

    if {"salary_min", "salary_max"}.issubset(df.columns):

        salary_min = pd.to_numeric(
            df["salary_min"],
            errors="coerce"
        )

        salary_max = pd.to_numeric(
            df["salary_max"],
            errors="coerce"
        )

        invalid_ranges = (
            salary_min.notna()
            & salary_max.notna()
            & (salary_min > salary_max)
        ).sum()

        print(
            f"Invalid salary ranges (min > max): "
            f"{invalid_ranges:,}"
        )

    # ---------------------------------------------------------
    # 5. ROLE CLASSIFICATION
    # ---------------------------------------------------------
    print("\n5. ROLE CLASSIFICATION")
    print("-" * 65)

    if "standard_role" in df.columns:

        missing_roles = df["standard_role"].isna().sum()

        print(
            f"Jobs without standard role: "
            f"{missing_roles:,}"
        )

        print("\nTop 20 standard roles:")

        print(
            df["standard_role"]
            .value_counts(dropna=False)
            .head(20)
            .to_string()
        )

    # ---------------------------------------------------------
    # 6. ROLE FAMILIES
    # ---------------------------------------------------------
    print("\n6. ROLE FAMILIES")
    print("-" * 65)

    if "role_family" in df.columns:

        print(
            df["role_family"]
            .value_counts(dropna=False)
            .to_string()
        )

    # ---------------------------------------------------------
    # 7. SENIORITY
    # ---------------------------------------------------------
    print("\n7. SENIORITY")
    print("-" * 65)

    if "seniority" in df.columns:

        seniority_counts = (
            df["seniority"]
            .value_counts(dropna=False)
        )

        for level, count in seniority_counts.items():

            percentage = count / len(df)

            print(
                f"{str(level):<22} "
                f"{count:>5,} "
                f"({percentage:>6.1%})"
            )

    # ---------------------------------------------------------
    # 8. SKILL EXTRACTION
    # ---------------------------------------------------------
    print("\n8. SKILL EXTRACTION")
    print("-" * 65)

    if "skill_count" in df.columns:

        print(
            f"Average detected skills/job: "
            f"{df['skill_count'].mean():.2f}"
        )

        print(
            f"Median detected skills/job: "
            f"{df['skill_count'].median():.0f}"
        )

        zero_skills = (df["skill_count"] == 0).sum()

        print(
            f"Jobs with zero detected skills: "
            f"{zero_skills:,} "
            f"({zero_skills / len(df):.1%})"
        )

    if "skills" in df.columns:

        skills = (
            df["skills"]
            .dropna()
            .astype(str)
            .str.split("|")
            .explode()
        )

        skills = skills[
            skills.str.strip().ne("")
        ]

        if not skills.empty:

            print("\nTop 20 detected skills:")

            print(
                skills
                .value_counts()
                .head(20)
                .to_string()
            )

    # ---------------------------------------------------------
    # 9. DESCRIPTION QUALITY
    # ---------------------------------------------------------
    print("\n9. DESCRIPTION QUALITY")
    print("-" * 65)

    if "description" in df.columns:

        lengths = (
            df["description"]
            .fillna("")
            .astype(str)
            .str.len()
        )

        print(
            f"Median description length: "
            f"{lengths.median():,.0f} characters"
        )

        print(
            f"Average description length: "
            f"{lengths.mean():,.0f} characters"
        )

        short_descriptions = (lengths < 200).sum()

        print(
            f"Descriptions <200 characters: "
            f"{short_descriptions:,} "
            f"({short_descriptions / len(df):.1%})"
        )

    # ---------------------------------------------------------
    # FINAL STATUS
    # ---------------------------------------------------------
    print("\n" + "=" * 65)
    print("QUALITY REPORT COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    main()