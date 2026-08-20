import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    RAW_DIR,
    REFERENCE_DIR,
)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search"


# ---------------------------------------------------------
# Core role queries
# ---------------------------------------------------------

CORE_ROLES = [
    "Data Analyst",
    "Business Analyst",
    "Data Scientist",
    "Data Engineer",
    "Software Developer",
    "Cyber Security",
    "Cloud Engineer",
    "Web Developer",
]


# ---------------------------------------------------------
# Credentials
# ---------------------------------------------------------

def require_credentials() -> None:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError(
            "Missing Adzuna credentials. "
            "Add ADZUNA_APP_ID and ADZUNA_APP_KEY to .env."
        )


# ---------------------------------------------------------
# API request
# ---------------------------------------------------------

def fetch_jobs(
    role: str,
    pages: int = 3,
    results_per_page: int = 50,
    pause: float = 0.25,
) -> list[dict]:

    require_credentials()

    jobs = []

    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "LondonTechJobAnalyzer/0.2",
        }
    )

    for page in range(1, pages + 1):

        url = f"{BASE_URL}/{page}"

        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": results_per_page,
            "what": role,
            "where": "London",
            "content-type": "application/json",
        }

        try:
            response = session.get(
                url,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            print(
                f"WARNING: request failed for "
                f"{role}, page {page}: {exc}"
            )
            continue

        payload = response.json()

        results = payload.get("results", [])

        print(
            f"   Page {page}: "
            f"{len(results)} adverts"
        )

        collected_at = datetime.now(
            timezone.utc
        ).isoformat()

        for job in results:

            location = job.get("location") or {}
            company = job.get("company") or {}
            category = job.get("category") or {}

            description = job.get("description")

            jobs.append(
                {
                    "job_id": str(job.get("id", "")),
                    "raw_title": job.get("title"),
                    "company": company.get("display_name"),
                    "location": location.get("display_name"),
                    "location_area": " > ".join(
                        location.get("area", []) or []
                    ),
                    "description": description,
                    "description_length": (
                        len(description)
                        if isinstance(description, str)
                        else 0
                    ),
                    "created": job.get("created"),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "salary_predicted": job.get(
                        "salary_is_predicted"
                    ),
                    "contract_type": job.get(
                        "contract_type"
                    ),
                    "contract_time": job.get(
                        "contract_time"
                    ),
                    "category": category.get("label"),
                    "redirect_url": job.get(
                        "redirect_url"
                    ),
                    "latitude": job.get("latitude"),
                    "longitude": job.get("longitude"),
                    "search_role": role,
                    "source": "Adzuna",
                    "collected_at": collected_at,
                }
            )

        time.sleep(pause)

    return jobs


# ---------------------------------------------------------
# Multi-role collection
# ---------------------------------------------------------

def collect_all_jobs(
    roles: list[str],
    pages: int,
    results_per_page: int,
):
    all_results = []

    for idx, role in enumerate(
        roles,
        start=1,
    ):

        print(
            f"\n[{idx}/{len(roles)}] "
            f"Collecting: {role}"
        )

        results = fetch_jobs(
            role,
            pages=pages,
            results_per_page=results_per_page,
        )

        all_results.extend(results)

    matches_df = pd.DataFrame(all_results)

    if matches_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # -----------------------------------------------------
    # Query-match table
    #
    # Keeps the relationship:
    # job advert <-> search query
    # -----------------------------------------------------

    query_matches = (
        matches_df[
            [
                "job_id",
                "search_role",
                "collected_at",
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # -----------------------------------------------------
    # Unique advert table
    # -----------------------------------------------------

    unique_jobs = (
        matches_df
        .sort_values("collected_at")
        .drop_duplicates(
            subset=["job_id"],
            keep="last",
        )
        .copy()
    )

    # Save all search roles that matched each advert
    role_matches = (
        matches_df.groupby("job_id")["search_role"]
        .apply(
            lambda values: " | ".join(
                sorted(set(values))
            )
        )
        .rename("matched_search_roles")
    )

    unique_jobs = unique_jobs.drop(
        columns=["search_role"]
    )

    unique_jobs = unique_jobs.merge(
        role_matches,
        on="job_id",
        how="left",
    )

    # -----------------------------------------------------
    # Advertiser concentration
    # -----------------------------------------------------

    company_counts = (
        unique_jobs["company"]
        .fillna("Unknown")
        .value_counts()
    )

    unique_jobs["advertiser_frequency"] = (
        unique_jobs["company"]
        .fillna("Unknown")
        .map(company_counts)
    )

    # -----------------------------------------------------
    # Salary availability flag
    # -----------------------------------------------------

    unique_jobs["salary_available"] = (
        unique_jobs["salary_min"].notna()
        | unique_jobs["salary_max"].notna()
    )

    # -----------------------------------------------------
    # Description truncation flag
    #
    # Our pilot showed Adzuna descriptions at exactly
    # 500 characters. We keep the flag rather than
    # pretending that this is complete job text.
    # -----------------------------------------------------

    unique_jobs["description_likely_truncated"] = (
        unique_jobs["description_length"] >= 500
    )

    return (
        unique_jobs.reset_index(drop=True),
        query_matches,
    )


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_collection(
    jobs: pd.DataFrame,
    query_matches: pd.DataFrame,
):

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    jobs_file = (
        RAW_DIR
        / f"adzuna_jobs_{stamp}.csv"
    )

    matches_file = (
        RAW_DIR
        / f"adzuna_query_matches_{stamp}.csv"
    )

    jobs.to_csv(
        jobs_file,
        index=False,
    )

    query_matches.to_csv(
        matches_file,
        index=False,
    )

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)

    print(
        f"Unique adverts: "
        f"{len(jobs):,}"
    )

    print(
        f"Query matches: "
        f"{len(query_matches):,}"
    )

    print(
        f"Unique companies: "
        f"{jobs['company'].nunique():,}"
    )

    print(
        f"Salary coverage: "
        f"{jobs['salary_available'].mean():.1%}"
    )

    print(
        f"Descriptions likely truncated: "
        f"{jobs['description_likely_truncated'].mean():.1%}"
    )

    print(f"\nJobs saved to:\n{jobs_file}")
    print(
        f"\nQuery matches saved to:\n"
        f"{matches_file}"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Collect London technology jobs "
            "from the Adzuna API."
        )
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Pages per role",
    )

    parser.add_argument(
        "--results-per-page",
        type=int,
        default=50,
        help="Results per page",
    )

    parser.add_argument(
        "--role",
        type=str,
        default=None,
        help=(
            "Optional single role. "
            "Useful for testing."
        ),
    )

    args = parser.parse_args()

    if args.role:
        roles = [args.role]
    else:
        roles = CORE_ROLES

    print("=" * 60)
    print("LONDON TECH JOB MARKET COLLECTOR")
    print("=" * 60)

    print(
        f"Roles: {len(roles)}"
    )

    print(
        f"Maximum API requests: "
        f"{len(roles) * args.pages}"
    )

    print(
        f"Maximum raw results: "
        f"{len(roles) * args.pages * args.results_per_page:,}"
    )

    jobs, matches = collect_all_jobs(
        roles,
        pages=args.pages,
        results_per_page=args.results_per_page,
    )

    if jobs.empty:
        print("No jobs collected.")
        return

    save_collection(
        jobs,
        matches,
    )


if __name__ == "__main__":
    main()