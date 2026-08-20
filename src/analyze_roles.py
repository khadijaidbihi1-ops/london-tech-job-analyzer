from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

JOBS_FILE = PROCESSED_DIR / "jobs_processed.csv"
ONS_OCCUPATIONS_FILE = PROCESSED_DIR / "ons_occupation_skills_2025.csv"
ONS_TRENDS_FILE = PROCESSED_DIR / "ons_skill_trends.csv"

OUTPUT_FILE = PROCESSED_DIR / "role_analysis.csv"


# ---------------------------------------------------------
# Roles we want to analyse
# ---------------------------------------------------------

ROLE_MAP = {
    "data_analyst": {
        "label": "Data Analyst",
        "ons_occupation": "data_analysts",
    },
    "software_developer": {
        "label": "Software Developer",
        "ons_occupation": "programmers_and_software_development_professionals",
    },
    "web_developer": {
        "label": "Web Developer",
        "ons_occupation": "web_design_professionals",
    },
    "cyber_security": {
        "label": "Cyber Security",
        "ons_occupation": "cyber_security_professionals",
    },
    "it_support": {
        "label": "IT Support",
        "ons_occupation": "it_user_support_technicians",
    },
    "database_administrator": {
        "label": "Database Administrator",
        "ons_occupation": "database_administrators_and_web_content_technicians",
    },
    "network_professional": {
        "label": "Network Professional",
        "ons_occupation": "it_network_professionals",
    },
    "it_business_analyst": {
        "label": "IT Business Analyst",
        "ons_occupation": "it_business_analysts,_architects_and_systems_designers",
    },
}


def load_data():
    """Load the processed datasets."""

    jobs = pd.read_csv(JOBS_FILE)
    occupations = pd.read_csv(ONS_OCCUPATIONS_FILE)
    trends = pd.read_csv(ONS_TRENDS_FILE)

    return jobs, occupations, trends


def analyse_ons_role(occupations, occupation_name):
    """Return the strongest ONS competency areas for an occupation."""

    data = occupations[
        occupations["occupation"] == occupation_name
    ].copy()

    if data.empty:
        return []

    data = data.sort_values(
        "share",
        ascending=False
    )

    return data[
        ["skill_group", "share"]
    ].head(10).to_dict("records")


def analyse_jobs(jobs):
    """Calculate basic statistics for the current job sample."""

    result = {
        "vacancies": len(jobs),
        "companies": jobs["company"].nunique(),
    }

    salaries = pd.concat(
        [
            pd.to_numeric(jobs["salary_min"], errors="coerce"),
            pd.to_numeric(jobs["salary_max"], errors="coerce"),
        ]
    ).dropna()

    if not salaries.empty:
        result["median_salary"] = round(
            salaries.median(),
            2
        )
    else:
        result["median_salary"] = None

    return result


def build_role_analysis():
    jobs, occupations, trends = load_data()

    print("=" * 60)
    print("LONDON TECH JOB ANALYZER")
    print("=" * 60)

    print(f"\nCurrent job adverts: {len(jobs):,}")
    print(
        f"ONS occupations available: "
        f"{occupations['occupation'].nunique():,}"
    )

    job_stats = analyse_jobs(jobs)

    output_rows = []

    for role_id, config in ROLE_MAP.items():

        print("\n" + "-" * 60)
        print(config["label"].upper())
        print("-" * 60)

        competencies = analyse_ons_role(
            occupations,
            config["ons_occupation"]
        )

        if not competencies:
            print(
                f"ONS occupation not found: "
                f"{config['ons_occupation']}"
            )
            continue

        print("\nTop ONS competency areas:")

        for rank, competency in enumerate(
            competencies,
            start=1
        ):
            skill = competency["skill_group"]
            share = competency["share"]

            print(
                f"{rank:>2}. "
                f"{skill:<45} "
                f"{share:.3f}"
            )

            output_rows.append(
                {
                    "role_id": role_id,
                    "role": config["label"],
                    "ons_occupation": config["ons_occupation"],
                    "competency_rank": rank,
                    "competency": skill,
                    "share": share,
                    "current_job_sample": job_stats["vacancies"],
                    "companies_in_sample": job_stats["companies"],
                    "median_salary_sample": job_stats["median_salary"],
                }
            )

    output = pd.DataFrame(output_rows)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print(f"Rows created: {len(output):,}")
    print(f"Saved to: {OUTPUT_FILE}")

    return output


if __name__ == "__main__":
    build_role_analysis()