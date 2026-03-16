import os
import re
import json
import pandas as pd
import requests
import random
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:latest"

CV_FOLDER = "Generated CV'S"
JOB_FOLDER = "Generated Job Market"
EXTRACTED_TEXT_FOLDER = "extracted_text"

CV_SOURCE_MODE = "real_txt"   # use "synthetic" or "real_txt"
RANDOM_TEST_CV = True

# ---------- LOAD ALL FILES ----------

def load_all_xlsx(folder_path):
    all_dfs = []
    files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]
    for file in files:
        path = os.path.join(folder_path, file)
        df = pd.read_excel(path)
        df["source_file"] = file
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)


cvs = load_all_xlsx(CV_FOLDER)
jobs = load_all_xlsx(JOB_FOLDER)


# ---------- ROLE NORMALISATION ----------

ROLE_MAP = {
    "backend": ["backend", "software engineer (backend)", "backend developer"],
    "frontend": ["frontend", "frontend developer", "ui developer"],
    "data analyst": ["data analyst", "analytics", "bi analyst"],
    "data engineer": ["data engineer", "etl engineer"],
    "devops": ["devops", "platform engineer", "site reliability"],
    "ml engineer": ["ml engineer", "machine learning engineer", "ai engineer"],
}

LEVEL_ORDER = ["junior", "mid", "senior"]


def detect_role(text):
    text = str(text).lower()
    for canonical, variants in ROLE_MAP.items():
        for v in variants:
            if v in text:
                return canonical
    return "unknown"


def detect_level_from_cv(cv_row):
    exp_text = str(cv_row.get("experience", "")).lower()

    years = re.findall(r"(\d+)\+?\s*years?", exp_text)
    max_years = max([int(y) for y in years], default=0)

    if max_years >= 5:
        return "senior"
    if max_years >= 2:
        return "mid"
    return "junior"

def detect_level_from_job(job_row):
    title = str(job_row.get("job_title", "")).lower()
    level = str(job_row.get("seniority_level", "")).strip().lower()

    if "senior" in title:
        return "senior"
    if "junior" in title:
        return "junior"
    if "mid" in title or "mid-level" in title or "mid level" in title:
        return "mid"

    if level in LEVEL_ORDER:
        return level

    return "mid"


def load_latest_txt_file(folder_path):
    txt_files = list(Path(folder_path).glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError("No extracted TXT files found.")

    latest_file = max(txt_files, key=lambda f: f.stat().st_mtime)
    text = latest_file.read_text(encoding="utf-8", errors="ignore")
    return latest_file, text


def detect_role_from_text(text):
    text_lower = str(text).lower()

    keyword_map = {
        "backend": ["spring boot", "java", "rest api", "microservices", "backend"],
        "frontend": ["react", "javascript", "html", "css", "next.js", "frontend"],
        "data analyst": ["power bi", "tableau", "data analysis", "excel", "sql", "analytics"],
        "data engineer": ["etl", "airflow", "data pipeline", "spark", "snowflake", "redshift"],
        "devops": ["kubernetes", "docker", "terraform", "jenkins", "devops", "ci/cd"],
        "ml engineer": ["machine learning", "scikit-learn", "pytorch", "tensorflow", "model evaluation"],
    }

    scores = {}
    for role, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[role] = score

    best_role = max(scores, key=scores.get)
    if scores[best_role] == 0:
        return "unknown"
    return best_role


def detect_level_from_text(text):
    text_lower = str(text).lower()

    years = re.findall(r"(\d+)\+?\s*years?", text_lower)
    max_years = max([int(y) for y in years], default=0)

    if "senior" in text_lower or max_years >= 5:
        return "senior"
    if "mid" in text_lower or "mid-level" in text_lower or max_years >= 2:
        return "mid"
    return "junior"


def extract_skills_from_text(text, known_skills):
    text_lower = str(text).lower()
    found = []

    for skill in known_skills:
        skill_clean = str(skill).strip()
        if skill_clean and skill_clean.lower() in text_lower:
            found.append(skill_clean)

    return sorted(set(found), key=str.lower)


# ---------- PICK CV SOURCE ----------

if CV_SOURCE_MODE == "synthetic":
    if RANDOM_TEST_CV:
        random_index = random.randint(0, len(cvs) - 1)
    else:
        random_index = 0

    cv = cvs.iloc[random_index]
    cv_name = cv.get("full_name", "Synthetic CV")
    cv_source_field = cv.get("primary_field", "")
    cv_role = detect_role(cv_source_field)
    cv_level = detect_level_from_cv(cv)
    cv_skills_text = cv.get("technical_skills", "")

    print(f"Using synthetic CV row: {random_index}")

elif CV_SOURCE_MODE == "real_txt":
    txt_file, cv_text = load_latest_txt_file(EXTRACTED_TEXT_FOLDER)

    # build known skills from job market
    all_known_skills = []
    for _, job_row in jobs.iterrows():
        req = str(job_row.get("required_skills", ""))
        pref = str(job_row.get("preferred_skills", ""))
        all_known_skills.extend([s.strip() for s in req.split(",") if s.strip()])
        all_known_skills.extend([s.strip() for s in pref.split(",") if s.strip()])

    all_known_skills = sorted(set(all_known_skills), key=str.lower)

    cv_name = txt_file.stem
    cv_source_field = "Extracted from uploaded CV text"
    cv_role = detect_role_from_text(cv_text)
    cv_level = detect_level_from_text(cv_text)
    extracted_skills = extract_skills_from_text(cv_text, all_known_skills)
    cv_skills_text = ", ".join(extracted_skills)

    print(f"Using real TXT CV: {txt_file.name}")

else:
    raise ValueError("Invalid CV_SOURCE_MODE. Use 'synthetic' or 'real_txt'.")

# ---------- FILTER JOBS BY ROLE ----------

jobs["normalized_role"] = jobs["job_title"].apply(detect_role)
jobs["normalized_level"] = jobs.apply(detect_level_from_job, axis=1)

filtered_jobs = jobs[jobs["normalized_role"] == cv_role].copy()

if filtered_jobs.empty:
    print("No matching jobs found for role.")
    raise SystemExit

same_level_jobs = filtered_jobs[filtered_jobs["normalized_level"] == cv_level].copy()

if same_level_jobs.empty:
    same_level_jobs = filtered_jobs.copy()

# keep small for first test
candidate_jobs = same_level_jobs.copy()

# ---------- SCORE FIX ----------
def normalize_skill(skill):
    return str(skill).strip().lower()

def strict_skill_compare(user_skills, market_skills):
    user_skill_list = [s.strip() for s in str(user_skills).split(",") if s.strip()]
    market_skill_list = [s.strip() for s in market_skills if str(s).strip()]

    user_skill_map = {normalize_skill(s): s for s in user_skill_list}
    market_skill_map = {normalize_skill(s): s for s in market_skill_list}

    matched = []
    missing = []

    for norm_skill, original_skill in market_skill_map.items():
        if norm_skill in user_skill_map:
            matched.append(original_skill)
        else:
            missing.append(original_skill)

    fit_score = round((len(matched) / len(market_skill_list)) * 100) if market_skill_list else 0

    return matched, missing, fit_score


def get_alignment_label(fit_score):
    if fit_score >= 70:
        return "Strong Alignment"
    elif fit_score >= 40:
        return "Moderate Alignment"
    elif fit_score >= 20:
        return "Weak Alignment"
    else:
        return "Very Low Alignment"


def get_similarity_summary(fit_score, role_name):
    if fit_score >= 70:
        return f"Your CV is strongly aligned with the current {role_name} market profile."
    elif fit_score >= 40:
        return f"Your CV is moderately aligned with the current {role_name} market profile."
    elif fit_score >= 20:
        return f"Your CV has limited alignment with the current {role_name} market profile."
    else:
        return f"Your CV is currently not very similar to the skills employers are expecting in the {role_name} market."


# ---------- AI COMPARISON ----------
def compare_with_ai(matched_skills, missing_skills, fit_score, role_name):
    prompt = f"""
You are a skill gap analysis assistant.

Write a short, clear summary for the user.

Role:
{role_name}

Skills already present:
{", ".join(matched_skills)}

Skills missing or weaker:
{", ".join(missing_skills)}

Fit score:
{fit_score}%

Strict rules:
- speak directly to the user using only "you" and "your"
- never use the words "candidate", "applicant", or "person"
- do not rename, reword, correct, shorten, or invent any skill names
- only mention skills exactly as written above
- mention strengths first, then the main missing areas
- keep it short, practical, and professional
- return plain text only
- no markdown
"""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 220
            }
        },
        timeout=300
    )

    data = response.json()

    if "response" not in data:
        return f"Model error: {data}"

    return data["response"].strip()


from collections import Counter

all_required_skills = []
all_companies = []

for _, job in candidate_jobs.iterrows():
    skills_text = str(job.get("required_skills", ""))
    company = str(job.get("company_name", "")).strip()

    if company:
        all_companies.append(company)

    split_skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    all_required_skills.extend(split_skills)

skill_counts = Counter(all_required_skills)
top_required_skills = [skill for skill, count in skill_counts.most_common(20)]
unique_companies = sorted(set(all_companies))

matched_skills, missing_skills, fit_score = strict_skill_compare(
    cv_skills_text,
    top_required_skills
)

feedback_text = compare_with_ai(
    matched_skills=matched_skills,
    missing_skills=missing_skills,
    fit_score=fit_score,
    role_name=f"{cv_role} ({cv_level}) market demand summary"
)
feedback_text = feedback_text.replace("The candidate", "You")
feedback_text = feedback_text.replace("candidate", "you")
feedback_text = feedback_text.replace("Candidate", "You")
feedback_text = feedback_text.replace("The applicant", "You")
feedback_text = feedback_text.replace("applicant", "you")
feedback_text = feedback_text.replace("The user", "You")
feedback_text = feedback_text.replace("user", "you")

alignment_label = get_alignment_label(fit_score)
similarity_summary = get_similarity_summary(fit_score, cv_role)

print("\n========== SKILL GAP SUMMARY ==========")

print(f"\nCV File: {cv_name}")
print(f"Current / Source Field from CV: {cv_source_field}")
print(f"Detected Comparison Field: {cv_role}")
print(f"Estimated Level: {cv_level}")
print(f"Relevant Jobs Analysed in This Field: {len(candidate_jobs)}")

print("\nCompanies actively hiring for this profile:")
print(", ".join(unique_companies[:20]))
total_jobs = len(candidate_jobs)

high_demand = []
medium_demand = []
low_demand = []

for skill in top_required_skills:
    demand_count = skill_counts.get(skill, 0)
    demand_percent = round((demand_count / total_jobs) * 100, 1) if total_jobs else 0
    item = f"{skill} ({demand_percent}%)"

    if demand_percent >= 70:
        high_demand.append(item)
    elif demand_percent >= 30:
        medium_demand.append(item)
    else:
        low_demand.append(item)

print("\nMARKET DEMAND OVERVIEW:")

print("\nHigh-demand skills:")
for item in high_demand:
    print(f"- {item}")

print("\nMedium-demand skills:")
for item in medium_demand:
    print(f"- {item}")

print("\nLow-demand / niche skills:")
for item in low_demand:
    print(f"- {item}")

print("\nSKILLS YOU ALREADY HAVE:")
for skill in matched_skills:
    print(f"- {skill}")

print("\nSKILLS YOU MAY NEED TO IMPROVE OR ADD:")
for skill in missing_skills:
    print(f"- {skill}")

print(f"\nOVERALL FIT SCORE: {fit_score}%")
print(f"ROLE ALIGNMENT: {alignment_label}")

print("\nSIMILARITY SUMMARY:")
print(similarity_summary)

feedback_text = feedback_text.replace("The candidate", "You")
feedback_text = feedback_text.replace("candidate", "you")
feedback_text = feedback_text.replace("Candidate", "You")
feedback_text = feedback_text.replace("The applicant", "You")
feedback_text = feedback_text.replace("applicant", "you")
feedback_text = feedback_text.replace("The user", "You")
feedback_text = feedback_text.replace("user", "you")

print("\nWHAT THIS MEANS FOR YOU:")
print(feedback_text)