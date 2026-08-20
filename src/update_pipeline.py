import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR


CURRENT_FILE = PROCESSED_DIR / "jobs_processed.csv"
HISTORY_FILE = PROCESSED_DIR / "jobs_history.csv"
SNAPSHOTS_FILE = PROCESSED_DIR / "job_snapshots.csv"
UPDATE_LOG_FILE = PROCESSED_DIR / "update_log.csv"


def run_module(module_name: str) -> None:
    print(f"\n>>> Running {module_name}")
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{module_name} failed with exit code {result.returncode}"
        )


def current_snapshot_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def current_snapshot_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def month_already_saved(month: str) -> bool:
    snapshots = load_csv(SNAPSHOTS_FILE)

    if snapshots.empty or "snapshot_month" not in snapshots.columns:
        return False

    return month in set(
        snapshots["snapshot_month"]
        .dropna()
        .astype(str)
    )


def append_snapshot(
    current_df: pd.DataFrame,
    snapshot_month: str,
    snapshot_at: str,
    replace_month: bool = False,
) -> None:

    snapshots = load_csv(SNAPSHOTS_FILE)

    current_snapshot = current_df.copy()
    current_snapshot["snapshot_month"] = snapshot_month
    current_snapshot["snapshot_at"] = snapshot_at

    if not snapshots.empty and replace_month:
        snapshots = snapshots[
            snapshots["snapshot_month"].astype(str) != snapshot_month
        ].copy()

    snapshots = pd.concat(
        [snapshots, current_snapshot],
        ignore_index=True,
        sort=False,
    )

    # One row per job per monthly snapshot.
    if {"job_id", "snapshot_month"}.issubset(snapshots.columns):
        snapshots = (
            snapshots
            .sort_values("snapshot_at")
            .drop_duplicates(
                subset=["job_id", "snapshot_month"],
                keep="last",
            )
        )

    snapshots.to_csv(
        SNAPSHOTS_FILE,
        index=False,
    )


def update_master_history(
    current_df: pd.DataFrame,
    snapshot_month: str,
    snapshot_at: str,
) -> None:

    history = load_csv(HISTORY_FILE)

    current = current_df.copy()

    current["first_seen_at"] = snapshot_at
    current["last_seen_at"] = snapshot_at
    current["first_seen_month"] = snapshot_month
    current["last_seen_month"] = snapshot_month

    if history.empty:
        master = current

    else:
        # Preserve the original first-seen dates for existing jobs.
        first_seen_lookup = (
            history
            .set_index("job_id")[
                [
                    "first_seen_at",
                    "first_seen_month",
                ]
            ]
            .to_dict("index")
            if "job_id" in history.columns
            else {}
        )

        current["first_seen_at"] = current["job_id"].map(
            lambda job_id: first_seen_lookup.get(
                job_id,
                {},
            ).get(
                "first_seen_at",
                snapshot_at,
            )
        )

        current["first_seen_month"] = current["job_id"].map(
            lambda job_id: first_seen_lookup.get(
                job_id,
                {},
            ).get(
                "first_seen_month",
                snapshot_month,
            )
        )

        # Keep old jobs that were not present in this month's snapshot.
        old_not_current = history[
            ~history["job_id"].astype(str).isin(
                current["job_id"].astype(str)
            )
        ].copy()

        master = pd.concat(
            [old_not_current, current],
            ignore_index=True,
            sort=False,
        )

    # Always keep one row per unique advert in the master history.
    master = (
        master
        .sort_values("last_seen_at")
        .drop_duplicates(
            subset=["job_id"],
            keep="last",
        )
    )

    master.to_csv(
        HISTORY_FILE,
        index=False,
    )


def write_update_log(
    snapshot_month: str,
    snapshot_at: str,
    rows: int,
    mode: str,
) -> None:

    log = load_csv(UPDATE_LOG_FILE)

    row = pd.DataFrame(
        [
            {
                "snapshot_month": snapshot_month,
                "snapshot_at": snapshot_at,
                "rows": rows,
                "mode": mode,
            }
        ]
    )

    log = pd.concat(
        [log, row],
        ignore_index=True,
        sort=False,
    )

    log.to_csv(
        UPDATE_LOG_FILE,
        index=False,
    )


def save_current_snapshot(
    mode: str,
    replace_month: bool = False,
) -> None:

    if not CURRENT_FILE.exists():
        raise FileNotFoundError(
            "jobs_processed.csv does not exist. "
            "Run the processing pipeline first."
        )

    current_df = pd.read_csv(CURRENT_FILE)

    if current_df.empty:
        raise RuntimeError(
            "jobs_processed.csv is empty."
        )

    month = current_snapshot_month()
    snapshot_at = current_snapshot_at()

    append_snapshot(
        current_df=current_df,
        snapshot_month=month,
        snapshot_at=snapshot_at,
        replace_month=replace_month,
    )

    update_master_history(
        current_df=current_df,
        snapshot_month=month,
        snapshot_at=snapshot_at,
    )

    write_update_log(
        snapshot_month=month,
        snapshot_at=snapshot_at,
        rows=len(current_df),
        mode=mode,
    )

    print("\n" + "=" * 68)
    print("HISTORY UPDATED")
    print("=" * 68)
    print(f"Snapshot month: {month}")
    print(f"Snapshot adverts: {len(current_df):,}")
    print(f"Master history: {HISTORY_FILE}")
    print(f"Monthly snapshots: {SNAPSHOTS_FILE}")
    print(f"Update log: {UPDATE_LOG_FILE}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the monthly London Tech Job Analyzer data pipeline."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Recollect and replace the current month's snapshot "
            "even if it already exists."
        ),
    )

    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help=(
            "Use the existing jobs_processed.csv to create the first "
            "historical snapshot without calling the Adzuna API."
        ),
    )

    args = parser.parse_args()

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    month = current_snapshot_month()

    print("=" * 68)
    print("LONDON TECH JOB ANALYZER - MONTHLY UPDATE")
    print("=" * 68)
    print(f"Current month: {month}")

    if args.bootstrap:
        print(
            "\nBootstrap mode: using the existing processed dataset."
        )

        save_current_snapshot(
            mode="bootstrap",
            replace_month=args.force,
        )

        return

    if month_already_saved(month) and not args.force:
        print(
            f"\nDataset already updated for {month}."
        )
        print(
            "No API collection required."
        )
        print(
            "Use --force only if you intentionally want to refresh "
            "this month's snapshot."
        )
        return

    print(
        "\nStarting full monthly pipeline..."
    )

    run_module("src.collect_jobs")
    run_module("src.process_jobs")
    run_module("src.quality_report")
    run_module("src.market_analysis")
    run_module("src.analyze_skills")

    save_current_snapshot(
        mode="forced_refresh" if args.force else "monthly_update",
        replace_month=args.force,
    )

    print("\n" + "=" * 68)
    print("MONTHLY UPDATE COMPLETE")
    print("=" * 68)


if __name__ == "__main__":
    main()