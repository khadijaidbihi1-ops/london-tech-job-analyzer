from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="London Tech Job Market Analyzer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

CURRENT_FILE = PROCESSED_DIR / "jobs_processed.csv"
HISTORY_FILE = PROCESSED_DIR / "jobs_history.csv"
UPDATE_LOG_FILE = PROCESSED_DIR / "update_log.csv"
SKILLS_FILE = PROCESSED_DIR / "skills_analysis.csv"
SKILLS_BY_ROLE_FILE = PROCESSED_DIR / "skills_by_role.csv"


# =========================================================
# THEME
# =========================================================

ACCENT = "#6366F1"
ACCENT_2 = "#8B5CF6"
NAVY = "#0F172A"
NAVY_2 = "#111827"

st.markdown(
    f"""
    <style>
        .stApp {{
            background: #F7F8FC;
        }}

        .block-container {{
            max-width: 1450px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}

        h1, h2, h3, h4 {{
            letter-spacing: -0.035em;
            color: #111827;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {NAVY} 0%, {NAVY_2} 100%);
            border-right: 0;
        }}

        [data-testid="stSidebar"] * {{
            color: #F8FAFC;
        }}

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p {{
            color: #CBD5E1 !important;
        }}

        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            padding: 1.15rem 1.2rem;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(15,23,42,.045);
        }}

        .hero {{
            background:
                radial-gradient(circle at 82% 20%, rgba(139,92,246,.22), transparent 26%),
                radial-gradient(circle at 68% 78%, rgba(99,102,241,.18), transparent 24%),
                linear-gradient(135deg, #0F172A 0%, #111827 55%, #1E1B4B 100%);
            border-radius: 24px;
            padding: 2rem 2.25rem;
            margin-bottom: 1.65rem;
            color: white;
            box-shadow: 0 22px 50px rgba(15,23,42,.13);
        }}

        .hero h1 {{
            color: white !important;
            margin: 0 0 .45rem 0;
            font-size: 2.25rem !important;
        }}

        .hero p {{
            color: #CBD5E1;
            margin: 0;
            font-size: 1.02rem;
            max-width: 780px;
        }}

        .eyebrow {{
            display: inline-block;
            color: #C7D2FE;
            background: rgba(99,102,241,.18);
            border: 1px solid rgba(199,210,254,.18);
            padding: .32rem .65rem;
            border-radius: 999px;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
            margin-bottom: .9rem;
        }}

        .soft-note {{
            color: #6B7280;
            font-size: .91rem;
            line-height: 1.55;
        }}

        .advisor-box {{
            background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
            border: 1px solid #DDD6FE;
            border-radius: 20px;
            padding: 1.25rem 1.35rem;
            margin: .5rem 0 1rem 0;
        }}

        .skill-chip-good {{
            display: inline-block;
            background: #ECFDF5;
            color: #15803D;
            border: 1px solid #DCFCE7;
            border-radius: 999px;
            padding: .3rem .65rem;
            margin: .18rem .22rem .18rem 0;
            font-size: .82rem;
            font-weight: 650;
        }}

        .skill-chip-missing {{
            display: inline-block;
            background: #FFF7ED;
            color: #C2410C;
            border: 1px solid #FED7AA;
            border-radius: 999px;
            padding: .3rem .65rem;
            margin: .18rem .22rem .18rem 0;
            font-size: .82rem;
            font-weight: 650;
        }}

        div[data-testid="stDataFrame"] {{
            background: white;
            border-radius: 16px;
            border: 1px solid #E5E7EB;
            overflow: hidden;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATA
# =========================================================

@st.cache_data
def load_jobs():
    source = HISTORY_FILE if HISTORY_FILE.exists() else CURRENT_FILE

    if not source.exists():
        raise FileNotFoundError(
            "No processed job dataset found."
        )

    df = pd.read_csv(source)

    if "salary_annual" in df.columns:
        df["salary_annual"] = pd.to_numeric(
            df["salary_annual"],
            errors="coerce",
        )

    if "created" in df.columns:
        df["created"] = pd.to_datetime(
            df["created"],
            errors="coerce",
            utc=True,
        )

    return df


@st.cache_data
def load_skill_data():
    overall = (
        pd.read_csv(SKILLS_FILE)
        if SKILLS_FILE.exists()
        else pd.DataFrame()
    )

    by_role = (
        pd.read_csv(SKILLS_BY_ROLE_FILE)
        if SKILLS_BY_ROLE_FILE.exists()
        else pd.DataFrame()
    )

    return overall, by_role


@st.cache_data
def load_update_log():
    if not UPDATE_LOG_FILE.exists():
        return pd.DataFrame()

    log = pd.read_csv(UPDATE_LOG_FILE)

    if "snapshot_at" in log.columns:
        log["snapshot_at"] = pd.to_datetime(
            log["snapshot_at"],
            errors="coerce",
            utc=True,
        )

    return log


df = load_jobs()
skills_overall, skills_by_role = load_skill_data()
update_log = load_update_log()


# =========================================================
# HELPERS
# =========================================================

def plotly_layout(fig, height=440):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            color="#475569",
        ),
        margin=dict(
            l=5,
            r=55,
            t=18,
            b=5,
        ),
        showlegend=False,
    )

    fig.update_xaxes(
        gridcolor="#EEF2F7",
        zeroline=False,
    )

    fig.update_yaxes(
        gridcolor="#EEF2F7",
        zeroline=False,
    )

    return fig


def friendly_text(value):
    if pd.isna(value) or value in ("", "None", None):
        return "Not specified"

    return (
        str(value)
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )


def chips(items, class_name):
    if not items:
        return (
            "<span class='soft-note'>None</span>"
        )

    return "".join(
        f"<span class='{class_name}'>{item}</span>"
        for item in items
    )


def build_skill_tables(source_df: pd.DataFrame):
    """Build skill summaries from the currently selected period."""
    if "skills" not in source_df.columns or source_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    working = source_df[["job_id", "standard_role", "skills"]].copy()
    working["skill"] = (
        working["skills"]
        .fillna("")
        .astype(str)
        .str.split("|")
    )
    exploded = working.explode("skill")
    exploded["skill"] = exploded["skill"].fillna("").str.strip()
    exploded = exploded[exploded["skill"] != ""].copy()

    if exploded.empty:
        return pd.DataFrame(), pd.DataFrame()

    overall = (
        exploded.groupby("skill")["job_id"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index(name="job_adverts")
    )
    overall["share_of_jobs"] = (
        overall["job_adverts"] / len(source_df) * 100
    ).round(2)

    role_totals = (
        source_df.groupby("standard_role")["job_id"]
        .nunique()
        .rename("role_job_count")
        .reset_index()
    )
    by_role = (
        exploded.groupby(["standard_role", "skill"])["job_id"]
        .nunique()
        .reset_index(name="job_adverts")
        .merge(role_totals, on="standard_role", how="left")
    )
    by_role["share_of_role_jobs"] = (
        by_role["job_adverts"] / by_role["role_job_count"] * 100
    ).round(2)
    by_role = by_role.sort_values(
        ["standard_role", "job_adverts", "skill"],
        ascending=[True, False, True],
    )

    return overall, by_role


# =========================================================
# HERO
# =========================================================

last_update_text = "Current snapshot"

if not update_log.empty:
    latest_update = (
        update_log["snapshot_at"]
        .dropna()
        .max()
    )

    if pd.notna(latest_update):
        last_update_text = (
            latest_update.strftime("%d %b %Y")
        )

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">London labour-market intelligence</div>
        <h1>London Tech Job Market Analyzer</h1>
        <p>
            Explore demand, salaries, career accessibility and skill signals
            across London technology job adverts.
            &nbsp;·&nbsp; Last data update: {last_update_text}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR — TIME FILTER
# =========================================================

st.sidebar.markdown("## Market filters")
st.sidebar.caption(
    "Refine every chart and metric."
)

period_options = {
    "Last month": 1,
    "Last 3 months": 3,
    "Last 6 months": 6,
    "Last 12 months": 12,
    "All available data": None,
}

selected_period = st.sidebar.selectbox(
    "Period",
    options=list(period_options.keys()),
    index=4,
)

working_df = df.copy()

months = period_options[selected_period]

if months is not None and "created" in working_df.columns:
    latest_date = (
        working_df["created"]
        .dropna()
        .max()
    )

    if pd.notna(latest_date):
        cutoff = latest_date - pd.DateOffset(
            months=months
        )

        working_df = working_df[
            working_df["created"] >= cutoff
        ].copy()


# =========================================================
# SIDEBAR — MARKET FILTERS
# =========================================================

role_families = sorted(
    working_df["role_family"]
    .dropna()
    .unique()
)

selected_families = st.sidebar.multiselect(
    "Role family",
    options=role_families,
)

roles_available = working_df.copy()

if selected_families:
    roles_available = roles_available[
        roles_available["role_family"].isin(
            selected_families
        )
    ]

roles = sorted(
    roles_available["standard_role"]
    .dropna()
    .unique()
)

selected_roles = st.sidebar.multiselect(
    "Role",
    options=roles,
)

seniority_order = [
    "Entry / Graduate",
    "Junior",
    "Mid / Unspecified",
    "Senior",
    "Lead / Manager",
]

available_seniority = [
    item
    for item in seniority_order
    if item in working_df["seniority"]
    .dropna()
    .unique()
]

selected_seniority = st.sidebar.multiselect(
    "Seniority",
    options=available_seniority,
)

salary_filter_enabled = (
    st.sidebar.checkbox(
        "Filter by annual salary",
        value=False,
    )
)

salary_range = None

salary_values = (
    working_df["salary_annual"]
    .dropna()
)

if (
    salary_filter_enabled
    and not salary_values.empty
):
    min_salary = int(
        salary_values.quantile(0.01)
    )

    max_salary = int(
        salary_values.quantile(0.99)
    )

    salary_range = st.sidebar.slider(
        "Annual salary range",
        min_value=min_salary,
        max_value=max_salary,
        value=(
            min_salary,
            max_salary,
        ),
        step=1000,
        format="£%d",
    )

filtered_df = working_df.copy()

if selected_families:
    filtered_df = filtered_df[
        filtered_df["role_family"].isin(
            selected_families
        )
    ]

if selected_roles:
    filtered_df = filtered_df[
        filtered_df["standard_role"].isin(
            selected_roles
        )
    ]

if selected_seniority:
    filtered_df = filtered_df[
        filtered_df["seniority"].isin(
            selected_seniority
        )
    ]

if salary_range:
    low, high = salary_range

    filtered_df = filtered_df[
        filtered_df["salary_annual"].isna()
        | filtered_df["salary_annual"].between(
            low,
            high,
        )
    ]

st.sidebar.divider()
st.sidebar.caption(
    f"{selected_period} · "
    f"{len(filtered_df):,} adverts"
)


# =========================================================
# MARKET SNAPSHOT
# =========================================================

st.subheader("Market snapshot")

total_jobs = len(filtered_df)

median_salary = (
    filtered_df["salary_annual"]
    .median()
)

entry_jobs = (
    filtered_df["seniority"]
    .isin(
        [
            "Entry / Graduate",
            "Junior",
        ]
    )
    .sum()
)

entry_share = (
    entry_jobs
    / total_jobs
    * 100
    if total_jobs
    else 0
)

companies = (
    filtered_df["company"]
    .nunique()
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Job adverts",
    f"{total_jobs:,}",
)

k2.metric(
    "Median annual salary",
    (
        f"£{median_salary:,.0f}"
        if pd.notna(median_salary)
        else "N/A"
    ),
)

k3.metric(
    "Entry / junior share",
    f"{entry_share:.1f}%",
)

k4.metric(
    "Hiring companies",
    f"{companies:,}",
)

st.caption(
    f"Period: {selected_period}"
)

st.divider()


# =========================================================
# DEMAND + SALARY
# =========================================================

left, right = st.columns(2)

with left:
    st.subheader("Job demand by role")

    role_counts = (
        filtered_df["standard_role"]
        .value_counts()
        .head(12)
        .reset_index()
    )

    role_counts.columns = [
        "Role",
        "Jobs",
    ]

    role_counts = (
        role_counts
        .sort_values("Jobs")
    )

    if not role_counts.empty:
        fig = px.bar(
            role_counts,
            x="Jobs",
            y="Role",
            orientation="h",
            text="Jobs",
            color_discrete_sequence=[
                ACCENT
            ],
        )

        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x:,} adverts"
                "<extra></extra>"
            ),
        )

        fig.update_xaxes(
            range=[
                0,
                role_counts["Jobs"].max()
                * 1.16,
            ],
            title="Job adverts",
        )

        fig.update_yaxes(
            title=None
        )

        plotly_layout(
            fig,
            470,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:
        st.info(
            "No jobs match the selected filters."
        )


with right:
    st.subheader("Median salary by role")

    salary_summary = (
        filtered_df
        .dropna(
            subset=["salary_annual"]
        )
        .groupby(
            "standard_role"
        )
        .agg(
            median_salary=(
                "salary_annual",
                "median",
            ),
            observations=(
                "salary_annual",
                "count",
            ),
        )
        .reset_index()
    )

    salary_summary = (
        salary_summary[
            salary_summary["observations"]
            >= 10
        ]
        .sort_values(
            "median_salary"
        )
        .tail(12)
    )

    if not salary_summary.empty:
        fig = px.bar(
            salary_summary,
            x="median_salary",
            y="standard_role",
            orientation="h",
            text="median_salary",
            color_discrete_sequence=[
                ACCENT_2
            ],
        )

        fig.update_traces(
            texttemplate=(
                "£%{text:,.0f}"
            ),
            textposition="outside",
            cliponaxis=False,
            customdata=salary_summary[
                ["observations"]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Median: £%{x:,.0f}<br>"
                "Observations: "
                "%{customdata[0]:,}"
                "<extra></extra>"
            ),
        )

        fig.update_xaxes(
            range=[
                0,
                salary_summary[
                    "median_salary"
                ].max()
                * 1.20,
            ],
            title=(
                "Median annual salary (£)"
            ),
        )

        fig.update_yaxes(
            title=None
        )

        plotly_layout(
            fig,
            470,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        st.caption(
            "Only roles with at least "
            "10 valid salary observations."
        )


# =========================================================
# CAREER ACCESSIBILITY
# =========================================================

st.divider()
st.subheader("Career accessibility")

left, right = st.columns(2)

with left:
    st.markdown(
        "#### Entry-level opportunities"
    )

    entry = filtered_df[
        filtered_df["seniority"].isin(
            [
                "Entry / Graduate",
                "Junior",
            ]
        )
    ]

    entry_counts = (
        entry["standard_role"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    entry_counts.columns = [
        "Role",
        "Entry / junior adverts",
    ]

    entry_counts = (
        entry_counts
        .sort_values(
            "Entry / junior adverts"
        )
    )

    if not entry_counts.empty:
        fig = px.bar(
            entry_counts,
            x="Entry / junior adverts",
            y="Role",
            orientation="h",
            text="Entry / junior adverts",
            color_discrete_sequence=[
                ACCENT
            ],
        )

        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_xaxes(
            range=[
                0,
                entry_counts[
                    "Entry / junior adverts"
                ].max()
                * 1.16,
            ],
            title=(
                "Entry / junior adverts"
            ),
        )

        fig.update_yaxes(
            title=None
        )

        plotly_layout(
            fig,
            420,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


with right:
    st.markdown(
        "#### Seniority distribution"
    )

    seniority_counts = (
        filtered_df["seniority"]
        .value_counts()
        .reindex(
            seniority_order
        )
        .fillna(0)
        .reset_index()
    )

    seniority_counts.columns = [
        "Seniority",
        "Jobs",
    ]

    fig = px.bar(
        seniority_counts,
        x="Seniority",
        y="Jobs",
        text="Jobs",
        color_discrete_sequence=[
            ACCENT_2
        ],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_xaxes(
        title=None,
        tickangle=-22,
    )

    fig.update_yaxes(
        title="Job adverts",
    )

    plotly_layout(
        fig,
        420,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# =========================================================
# SKILLS INTELLIGENCE + CAREER ADVISOR
# =========================================================

st.divider()
st.subheader("Skills intelligence")

period_skills_overall, period_skills_by_role = build_skill_tables(filtered_df)

if period_skills_by_role.empty:
    st.info("No detected skills are available for the current filters.")
else:
    st.markdown(
        """
        <div class="soft-note">
            Skill signals are exploratory because most Adzuna descriptions
            in this dataset are truncated to roughly 500 characters.
            Skill charts follow the selected period and market filters.
        </div>
        """,
        unsafe_allow_html=True,
    )

    skill_tab, advisor_tab = st.tabs(
        ["Market skill signals", "Career advisor"]
    )

    with skill_tab:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Most frequently detected skills")
            top_skills = period_skills_overall.head(15).sort_values("job_adverts")

            if not top_skills.empty:
                fig = px.bar(
                    top_skills,
                    x="job_adverts",
                    y="skill",
                    orientation="h",
                    text="job_adverts",
                    color_discrete_sequence=[ACCENT],
                )
                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    customdata=top_skills[["share_of_jobs"]],
                    hovertemplate=(
                        "<b>%{y}</b><br>%{x:,} adverts<br>"
                        "%{customdata[0]:.1f}% of selected adverts"
                        "<extra></extra>"
                    ),
                )
                fig.update_xaxes(
                    range=[0, top_skills["job_adverts"].max() * 1.18],
                    title="Adverts mentioning skill",
                )
                fig.update_yaxes(title=None)
                plotly_layout(fig, 500)
                st.plotly_chart(fig, width="stretch")

        with col2:
            st.markdown("#### Skill signals by target role")

            skill_roles = sorted(
                period_skills_by_role["standard_role"].dropna().unique()
            )
            selected_skill_role = st.selectbox(
                "Choose a role",
                options=skill_roles,
                index=(
                    skill_roles.index("Data Analyst")
                    if "Data Analyst" in skill_roles
                    else 0
                ),
                key="skill_role_select",
            )

            role_skill_data = (
                period_skills_by_role[
                    period_skills_by_role["standard_role"] == selected_skill_role
                ]
                .head(12)
                .sort_values("job_adverts")
            )

            if not role_skill_data.empty:
                fig = px.bar(
                    role_skill_data,
                    x="job_adverts",
                    y="skill",
                    orientation="h",
                    text="job_adverts",
                    color_discrete_sequence=[ACCENT_2],
                )
                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    customdata=role_skill_data[["share_of_role_jobs"]],
                    hovertemplate=(
                        "<b>%{y}</b><br>%{x:,} adverts<br>"
                        "%{customdata[0]:.1f}% of selected role adverts"
                        "<extra></extra>"
                    ),
                )
                fig.update_xaxes(
                    range=[0, max(role_skill_data["job_adverts"].max() * 1.22, 1)],
                    title="Adverts mentioning skill",
                )
                fig.update_yaxes(title=None)
                plotly_layout(fig, 500)
                st.plotly_chart(fig, width="stretch")

    with advisor_tab:
        st.markdown(
            """
            <div class="advisor-box">
                <b>Career Advisor</b><br>
                Select a target role and the skills you already have.
                The comparison uses the currently selected period and market filters.
            </div>
            """,
            unsafe_allow_html=True,
        )

        advisor_roles = sorted(
            period_skills_by_role["standard_role"].dropna().unique()
        )
        target_role = st.selectbox(
            "Target role",
            options=advisor_roles,
            index=(
                advisor_roles.index("Data Analyst")
                if "Data Analyst" in advisor_roles
                else 0
            ),
            key="advisor_role",
        )

        target_skills_df = (
            period_skills_by_role[
                period_skills_by_role["standard_role"] == target_role
            ]
            .sort_values(["job_adverts", "share_of_role_jobs"], ascending=False)
            .head(12)
        )

        all_known_skills = sorted(period_skills_overall["skill"].dropna().unique())
        owned_skills = st.multiselect(
            "Skills you already have",
            options=all_known_skills,
            help="Select skills you can currently use with reasonable confidence.",
        )

        target_skills = target_skills_df["skill"].tolist()
        matching = [skill for skill in target_skills if skill in owned_skills]
        missing = [skill for skill in target_skills if skill not in owned_skills]

        weights = dict(
            zip(target_skills_df["skill"], target_skills_df["job_adverts"])
        )
        total_weight = sum(weights.values())
        covered_weight = sum(weights.get(skill, 0) for skill in matching)
        readiness = covered_weight / total_weight * 100 if total_weight else 0

        target_jobs_df = filtered_df[
            filtered_df["standard_role"] == target_role
        ]
        target_jobs = len(target_jobs_df)
        target_median = target_jobs_df["salary_annual"].median()
        target_entry = target_jobs_df["seniority"].isin(
            ["Entry / Graduate", "Junior"]
        ).sum()
        target_entry_share = (
            target_entry / target_jobs * 100 if target_jobs else 0
        )

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Market adverts", f"{target_jobs:,}")
        a2.metric(
            "Median salary",
            f"£{target_median:,.0f}" if pd.notna(target_median) else "N/A",
        )
        a3.metric("Entry / junior", f"{target_entry_share:.1f}%")
        a4.metric("Skill readiness", f"{readiness:.0f}%")

        st.markdown("#### Your matching skills")
        st.markdown(chips(matching, "skill-chip-good"), unsafe_allow_html=True)

        st.markdown("#### Priority skills to develop")
        st.markdown(chips(missing, "skill-chip-missing"), unsafe_allow_html=True)

        gap_df = target_skills_df[target_skills_df["skill"].isin(missing)].copy()
        if not gap_df.empty:
            gap_df["Priority"] = range(1, len(gap_df) + 1)
            gap_display = gap_df[
                ["Priority", "skill", "job_adverts", "share_of_role_jobs"]
            ].rename(
                columns={
                    "skill": "Skill",
                    "job_adverts": "Detected in adverts",
                    "share_of_role_jobs": "% of role adverts",
                }
            )
            st.dataframe(
                gap_display,
                width="stretch",
                hide_index=True,
                column_config={
                    "% of role adverts": st.column_config.NumberColumn(
                        "% of role adverts", format="%.1f%%"
                    )
                },
            )

        st.caption(
            "Readiness is a weighted comparison against detected skill signals, "
            "not a hiring probability or employability score."
        )


# =========================================================
# HIRING ACTIVITY
# =========================================================

st.divider()
st.subheader("Hiring activity")

company_counts = (
    filtered_df["company"]
    .dropna()
    .value_counts()
    .head(15)
    .reset_index()
)

company_counts.columns = [
    "Company",
    "Jobs",
]

company_counts = (
    company_counts
    .sort_values("Jobs")
)

if not company_counts.empty:
    fig = px.bar(
        company_counts,
        x="Jobs",
        y="Company",
        orientation="h",
        text="Jobs",
        color_discrete_sequence=[
            ACCENT
        ],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_xaxes(
        range=[
            0,
            company_counts[
                "Jobs"
            ].max()
            * 1.16,
        ],
        title="Job adverts",
    )

    fig.update_yaxes(
        title=None
    )

    plotly_layout(
        fig,
        520,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

st.caption(
    "Recruitment agencies and direct employers are currently shown together."
)


# =========================================================
# JOB EXPLORER
# =========================================================

st.divider()
st.subheader("Job explorer")

display_df = filtered_df.copy()

for column in [
    "contract_type",
    "contract_time",
]:
    if column in display_df.columns:
        display_df[column] = (
            display_df[column]
            .apply(
                friendly_text
            )
        )

if "salary_annual" in display_df.columns:
    display_df[
        "salary_annual"
    ] = (
        display_df[
            "salary_annual"
        ]
        .round(0)
    )

job_columns = [
    "raw_title",
    "company",
    "standard_role",
    "role_family",
    "seniority",
    "salary_annual",
    "created",
    "contract_type",
    "contract_time",
]

job_columns = [
    column
    for column in job_columns
    if column in display_df.columns
]

st.dataframe(
    display_df[
        job_columns
    ],
    width="stretch",
    hide_index=True,
    column_config={
        "raw_title":
            "Job title",
        "company":
            "Company",
        "standard_role":
            "Standard role",
        "role_family":
            "Role family",
        "seniority":
            "Seniority",
        "salary_annual":
            st.column_config.NumberColumn(
                "Annual salary",
                format="£%.0f",
            ),
        "created":
            st.column_config.DatetimeColumn(
                "Posted",
                format="DD MMM YYYY",
            ),
        "contract_type":
            "Contract",
        "contract_time":
            "Working pattern",
    },
)


# =========================================================
# METHODOLOGY
# =========================================================

st.divider()

with st.expander(
    "Data, limitations & methodology"
):
    st.markdown(
        """
        **Historical storage**

        Monthly runs preserve a unique master history of adverts and a
        separate job-by-month snapshot table. The dashboard period filter
        uses the advert's own publication date (`created`) rather than the
        collection date.

        **Current market source**

        London technology adverts are collected through the Adzuna API.

        **Salary handling**

        Ambiguous pay periods are excluded from annual salary calculations
        rather than automatically annualised.

        **Skills**

        Most available descriptions are truncated to roughly 500 characters,
        so skill analysis is exploratory and should be interpreted as a
        lower-bound signal.

        **Career Advisor**

        Skill readiness is a weighted comparison with detected skill signals.
        It is not an employability or hiring-probability score.
        """
    )


st.caption(
    f"London Tech Job Market Analyzer · "
    f"{len(df):,} adverts in available history · "
    f"{len(filtered_df):,} currently displayed"
)
