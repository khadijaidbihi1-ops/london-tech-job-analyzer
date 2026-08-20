from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "ons_skills_2017_2025.xlsx"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

SKILL_TRENDS_FILE = OUTPUT_DIR / "ons_skill_trends.csv"
OCCUPATION_SKILLS_FILE = OUTPUT_DIR / "ons_occupation_skills_2025.csv"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def clean_column_name(column):
    """Convert Excel column names into consistent snake_case names."""
    column = str(column).strip().lower()

    replacements = {
        " ": "_",
        "-": "_",
        "/": "_",
        "(": "",
        ")": "",
    }

    for old, new in replacements.items():
        column = column.replace(old, new)

    while "__" in column:
        column = column.replace("__", "_")

    return column.strip("_")


def read_ons_table(sheet_name):
    """
    ONS worksheets contain five metadata rows.
    Row 6 in Excel (index 5) contains the real column headers.
    """
    df = pd.read_excel(
        INPUT_FILE,
        sheet_name=sheet_name,
        header=5
    )

    df.columns = [clean_column_name(col) for col in df.columns]

    # Remove completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    return df


# ---------------------------------------------------------
# Table 1
# Historical skill trends: 2017–2025
# ---------------------------------------------------------

def process_skill_trends():
    print("Processing ONS Table 1...")

    df = read_ons_table("Table 1")

    print(f"Raw rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    year_columns = [
        col for col in df.columns
        if col in {
            "2017",
            "2018",
            "2019",
            "2020",
            "2021",
            "2022",
            "2023",
            "2024",
            "2025",
        }
    ]

    id_columns = [
        col for col in df.columns
        if col not in year_columns
    ]

    # Wide → long format
    trends = df.melt(
        id_vars=id_columns,
        value_vars=year_columns,
        var_name="year",
        value_name="share"
    )

    trends["year"] = pd.to_numeric(
        trends["year"],
        errors="coerce"
    ).astype("Int64")

    trends["share"] = pd.to_numeric(
        trends["share"],
        errors="coerce"
    )

    trends = trends.dropna(
        subset=[
            "sco_most_detailed_level_label",
            "year",
            "share"
        ]
    )

    trends = trends.rename(
        columns={
            "sco_least_detailed_level_code":
                "skill_family_code",

            "sco_least_detailed_level_label":
                "skill_family",

            "sco_middle_level_code":
                "skill_group_code",

            "sco_middle_level_label":
                "skill_group",

            "sco_most_detailed_level_code":
                "skill_code",

            "sco_most_detailed_level_label":
                "skill",

            "sco_most_detailed_level_description":
                "skill_description",
        }
    )

    trends = trends[
        [
            "skill_family_code",
            "skill_family",
            "skill_group_code",
            "skill_group",
            "skill_code",
            "skill",
            "skill_description",
            "year",
            "share",
        ]
    ]

    trends.to_csv(
        SKILL_TRENDS_FILE,
        index=False
    )

    print(
        f"Saved {len(trends):,} rows to "
        f"{SKILL_TRENDS_FILE}"
    )

    return trends


# ---------------------------------------------------------
# Table 4
# Occupation × skill data for 2025
# ---------------------------------------------------------

def process_occupation_skills():
    print("\nProcessing ONS Table 4...")

    df = read_ons_table("Table 4")

    print(f"Raw rows: {len(df):,}")
    print(f"Raw columns: {len(df.columns):,}")

    # -----------------------------------------------------
    # Table 4 structure
    #
    # First 4 columns = SCO skill hierarchy
    # Remaining columns = SOC 2020 occupations
    # First data row = SOC codes for those occupations
    # -----------------------------------------------------

    skill_columns = list(df.columns[:4])
    occupation_columns = list(df.columns[4:])

    # First row contains SOC codes
    soc_codes = df.iloc[0][occupation_columns]

    occupation_lookup = {
        occupation: soc_codes[occupation]
        for occupation in occupation_columns
    }

    # Remove SOC-code metadata row
    df = df.iloc[1:].copy()

    # Rename skill metadata columns
    df = df.rename(
        columns={
            skill_columns[0]: "skill_family_code",
            skill_columns[1]: "skill_family",
            skill_columns[2]: "skill_group_code",
            skill_columns[3]: "skill_group",
        }
    )

    # Wide -> long
    long_df = df.melt(
        id_vars=[
            "skill_family_code",
            "skill_family",
            "skill_group_code",
            "skill_group",
        ],
        value_vars=occupation_columns,
        var_name="occupation",
        value_name="share",
    )

    # Add SOC code
    long_df["soc_code"] = long_df["occupation"].map(
        occupation_lookup
    )

    long_df["soc_code"] = (
        pd.to_numeric(
            long_df["soc_code"],
            errors="coerce"
        )
        .astype("Int64")
        .astype("string")
    )

    long_df["share"] = pd.to_numeric(
        long_df["share"],
        errors="coerce"
    )

    # Remove missing / unusable rows
    long_df = long_df.dropna(
        subset=[
            "skill_group",
            "occupation",
            "share"
        ]
    )

    # Remove zero-demand combinations.
    # Keeping them would make the dataset unnecessarily huge.
    long_df = long_df[
        long_df["share"] > 0
    ].copy()

    # Friendlier occupation labels
    long_df["occupation_label"] = (
        long_df["occupation"]
        .str.replace("_", " ", regex=False)
        .str.replace("n.e.c.", "n.e.c.", regex=False)
        .str.title()
    )

    long_df = long_df[
        [
            "soc_code",
            "occupation",
            "occupation_label",
            "skill_family_code",
            "skill_family",
            "skill_group_code",
            "skill_group",
            "share",
        ]
    ]

    long_df = long_df.sort_values(
        ["occupation", "share"],
        ascending=[True, False]
    )

    long_df.to_csv(
        OCCUPATION_SKILLS_FILE,
        index=False
    )

    print(
        f"Saved {len(long_df):,} occupation-skill "
        f"records to {OCCUPATION_SKILLS_FILE}"
    )

    print(
        f"Unique occupations: "
        f"{long_df['occupation'].nunique():,}"
    )

    print(
        f"Unique skill groups: "
        f"{long_df['skill_group'].nunique():,}"
    )

    return long_df

# ---------------------------------------------------------
# Quality summary
# ---------------------------------------------------------

def print_summary(trends, occupation_skills):
    print("\n" + "=" * 60)
    print("ONS PROCESSING SUMMARY")
    print("=" * 60)

    print(
        f"Historical skill records: "
        f"{len(trends):,}"
    )

    print(
        f"Unique detailed skills: "
        f"{trends['skill'].nunique():,}"
    )

    print(
        f"Years: "
        f"{trends['year'].min()}–"
        f"{trends['year'].max()}"
    )

    print(
        f"Table 4 records: "
        f"{len(occupation_skills):,}"
    )

    print("=" * 60)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"ONS file not found:\n{INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    trends = process_skill_trends()

    occupation_skills = process_occupation_skills()

    print_summary(
        trends,
        occupation_skills
    )


if __name__ == "__main__":
    main()