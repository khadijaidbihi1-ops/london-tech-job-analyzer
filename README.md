# London Tech Job Market Analyzer

An end-to-end Python data product for exploring London's technology labour market. The project collects live job adverts from the Adzuna API, cleans and normalises them, analyses salaries and seniority, extracts technical skill signals, stores monthly history, and exposes the results through an interactive Streamlit dashboard.

## What the project does

- Collects London job adverts across core technology roles from the Adzuna API.
- Deduplicates adverts found through multiple search queries while preserving query provenance.
- Normalises noisy job titles into consistent roles and role families.
- Infers seniority from job-title and description signals.
- Validates salary values and excludes ambiguous pay periods from annual salary analysis.
- Extracts technical skills using an explainable taxonomy and alias rules.
- Provides market-demand, salary, career-accessibility and hiring-company analysis.
- Includes a Career Advisor that compares a user's selected skills with detected market signals for a target role.
- Preserves monthly snapshots and a cumulative unique-advert history.
- Supports dashboard filters for the last month, 3 months, 6 months, 12 months, or all available data.
- Can refresh automatically each month with GitHub Actions.

## Dashboard

The Streamlit application includes:

- Market snapshot KPIs
- Demand by standard role
- Median salary by role
- Entry/junior opportunities
- Seniority distribution
- Skills intelligence
- Career Advisor / skill-gap view
- Hiring activity
- Filterable job explorer
- Time-period filtering
- Data-quality and methodology notes

Run it locally with:

```powershell
python -m streamlit run dashboard.py
```

## Project structure

```text
London_Tech_Job_Analyzer_Phase1/
├── .github/
│   └── workflows/
│       └── monthly_update.yml
├── data/
│   ├── outputs/              # Exported static charts
│   ├── processed/            # Dashboard-ready and historical datasets
│   ├── raw/                  # Local API pulls; ignored by Git
│   └── reference/            # Role/skill taxonomies and optional ONS source
├── notebooks/
├── src/
│   ├── analyze_roles.py
│   ├── analyze_skills.py
│   ├── collect_jobs.py
│   ├── config.py
│   ├── market_analysis.py
│   ├── normalize.py
│   ├── process_jobs.py
│   ├── process_ons.py
│   ├── quality_report.py
│   ├── update_pipeline.py
│   └── visualize_market.py
├── tests/
│   └── test_normalize.py
├── .env.example
├── .gitignore
├── dashboard.py
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure Adzuna credentials

Create a local `.env` file from `.env.example`:

```text
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
```

Never commit `.env` or real API credentials.

## Data pipeline

### Quick collection test

```powershell
python -m src.collect_jobs --role "Data Analyst" --pages 1 --results-per-page 20
python -m src.process_jobs
python -m src.quality_report
```

### Full current-market run

```powershell
python -m src.collect_jobs
python -m src.process_jobs
python -m src.quality_report
python -m src.market_analysis
python -m src.analyze_skills
```

### Monthly historical update

For the first existing dataset only:

```powershell
python -m src.update_pipeline --bootstrap
```

For subsequent months:

```powershell
python -m src.update_pipeline
```

To intentionally recollect the current month:

```powershell
python -m src.update_pipeline --force
```

The monthly pipeline maintains:

- `data/processed/jobs_processed.csv` — current processed snapshot
- `data/processed/jobs_history.csv` — one current record per unique advert seen across all runs
- `data/processed/job_snapshots.csv` — advert-by-month snapshot history
- `data/processed/update_log.csv` — update metadata

The dashboard time filter uses each advert's publication date (`created`).

## Automated monthly refresh

The repository includes `.github/workflows/monthly_update.yml`, scheduled for the first day of each month at 06:00 UTC.

Before enabling it, add these repository secrets in GitHub:

- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`

The workflow runs the monthly pipeline and commits refreshed files under `data/processed`. A Streamlit deployment connected to the repository can then redeploy from the new commit.

## Methodology

### Job classification

Employer titles are normalised with deterministic regular-expression rules. The original title and matching search role remain available so classification decisions are auditable.

### Seniority

Seniority is inferred from job-title and description keywords. `Mid / Unspecified` means no sufficiently reliable entry, junior, senior, lead, manager or director signal was detected; it is not necessarily a true mid-level role.

### Salary

The pipeline calculates a salary midpoint from the advertised minimum and maximum. Very low values that cannot safely be interpreted as annual salaries are marked as ambiguous and excluded from `salary_annual`. High annual outliers are retained but flagged. Role-level dashboard salary charts require at least 10 observations.

### Skills

Skills are extracted from job titles and descriptions using a controlled taxonomy in `data/reference/skills.json`. The Adzuna descriptions available in this sample are usually truncated to roughly 500 characters, so skill results are intentionally described as exploratory lower-bound signals rather than complete requirement frequencies.

### Career Advisor

The readiness percentage is a weighted comparison between the skills selected by the user and the skill signals detected for the selected target role. It is not an employability score, hiring probability, or career guarantee.

## Current sample

The included processed snapshot contains 1,184 unique London job adverts. The project is designed to grow through monthly refreshes rather than treat this initial sample as a permanent market baseline.

## Tests

Run:

```powershell
python -m pytest -q
```

The current tests validate core role, seniority and skill-normalisation behaviour.

## Optional ONS reference data

`process_ons.py` prepares an ONS skills dataset supplied under `data/reference`. This is supporting reference work and is not required by the current Streamlit dashboard.

## Technology

Python · pandas · requests · Streamlit · Plotly · pytest · GitHub Actions · Adzuna API

## Limitations

- API search results are a sample of the market rather than a census of all London vacancies.
- One advertiser may be a recruitment agency representing multiple employers.
- Job descriptions may be truncated by the source API.
- Seniority and role normalisation are rule-based and therefore imperfect.
- Historical trend analysis becomes more meaningful only after multiple monthly snapshots have accumulated.

## Responsible use

Do not commit API keys or local `.env` files. Before redistributing raw third-party job-advert content publicly, review the applicable API/provider terms. The public portfolio version can rely on processed analytical outputs rather than raw API responses.
