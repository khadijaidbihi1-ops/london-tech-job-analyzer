# Final Project Audit

## Status

The project compiles successfully and all automated tests pass (8/8).

## Corrections applied

- Renamed `src/update-pipeline.py` to `src/update_pipeline.py` so `python -m src.update_pipeline` works.
- Removed the local `.env` file from the public-ready copy.
- Added a root `.env.example` with placeholders only.
- Expanded `.gitignore` to protect secrets, caches, virtual environments and reproducible raw API pulls.
- Added `openpyxl` to `requirements.txt` because `src/process_ons.py` reads Excel workbooks.
- Replaced deprecated Streamlit `use_container_width=True` usage with `width="stretch"`.
- Made Skills Intelligence and the Career Advisor follow the active period and market filters instead of relying only on the latest precomputed skill CSV.
- Made Career Advisor role metrics follow the active filters.
- Created the initial historical snapshot files from the existing 1,184-advert dataset.
- Added a scheduled GitHub Actions workflow for monthly refreshes.
- Rewrote README for the complete v1.0 workflow and methodology.
- Expanded unit tests from 4 to 8 checks.
- Removed Python/test cache artifacts and raw API pulls from the public-ready copy.

## Important security action

The original archive contained a populated `.env` file. Do not upload that original archive to GitHub. Rotate the Adzuna API key before public deployment because the credential has already been shared outside the local machine.

## Current data notes

- 1,184 unique processed adverts in the initial snapshot.
- 99%+ have a salary value considered usable for annual analysis under the current validation rules.
- Skill detection coverage is low (~15%) because available descriptions are usually truncated; the dashboard labels skill analysis as exploratory.
- Historical trend analysis will become materially more useful after several monthly snapshots accumulate.

## Deployment note

A local monthly script alone does not provide cloud automation. The added GitHub Actions workflow performs the scheduled monthly update and commits refreshed processed datasets. GitHub repository secrets must be configured before enabling it.
