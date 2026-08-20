from src.normalize import classify_seniority, extract_skills, standardize_role


def test_power_bi_and_sql_normalization():
    skills = extract_skills("Strong SQL skills and Microsoft Power BI experience required.")
    assert "SQL" in skills
    assert "Power BI" in skills


def test_aws_alias():
    assert "AWS" in extract_skills("Experience with Amazon Web Services is preferred")


def test_role_title():
    assert standardize_role("Senior Machine Learning Engineer") == "Machine Learning Engineer"


def test_seniority():
    assert classify_seniority("Junior Data Analyst") == "Junior"
    assert classify_seniority("Senior Data Engineer") == "Senior"


def test_role_family_mapping():
    from src.normalize import role_family_for
    assert role_family_for("Data Analyst") == "Data & Analytics"
    assert role_family_for("Cloud Engineer") == "Cloud & Infrastructure"


def test_python_developer_normalization():
    assert standardize_role("Senior Python Developer") == "Python Developer"


def test_skill_aliases_are_deduplicated():
    skills = extract_skills("AWS and Amazon Web Services experience")
    assert skills.count("AWS") == 1


def test_leadership_seniority():
    assert classify_seniority("Head of Data") == "Lead / Manager"
