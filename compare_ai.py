import pandas as pd
import requests
import os

# LOAD DATASETS 

job_folder = "Generated Job Market"
cv_folder = "Generated CV'S"

job_files = [f for f in os.listdir(job_folder) if f.endswith(".xlsx")]
cv_files = [f for f in os.listdir(cv_folder) if f.endswith(".xlsx")]

job_data = []
cv_data = []

for file in job_files:
    df = pd.read_excel(os.path.join(job_folder, file))
    job_data.append(df)

for file in cv_files:
    df = pd.read_excel(os.path.join(cv_folder, file))
    cv_data.append(df)

jobs = pd.concat(job_data, ignore_index=True)
cvs = pd.concat(cv_data, ignore_index=True)

# PICK ONE CV AND ONE JOB

cv = cvs.iloc[0]
job = jobs.iloc[0]

cv_skills = cv["technical_skills"]
job_skills = job["required_skills"]

# BUILD AI PROMPT 

prompt = f"""
You are a skill gap analysis system.

Compare the user's skills against current market demand for this role.

User Skills:
{cv_skills}

Role Market Skills:
{job_skills}

Return valid JSON only:
{{
  "matched_skills": [],
  "missing_skills": [],
  "fit_score": 0,
  "feedback": ""
}}

Rules:
- fit_score must be from 0 to 100
- feedback must speak directly to the user using "you" and "your"
- do not use words like "candidate"
- keep feedback clear, short, and practical
- only return valid JSON
"""

# SEND TO PHI3

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "phi3",
        "prompt": prompt,
        "stream": False
    }
)

result = response.json()["response"]

print("\nAI RESULT:\n")
print(result)