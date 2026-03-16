import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

cv_text = open(r"C:\Users\kaush\OneDrive\Documents\uni 3rd year files\computing project 3rd year\assessment\assessment work in progress\CODE\extracted_text\CV - Example - Computing IT Data Science Web & AI - V2.txt", "r", encoding="utf-8").read()
job_data = {
    "role": "Machine Learning Engineer",
    "required_skills": ["Python", "SQL", "Docker", "TensorFlow"],
    "preferred_skills": ["Kubernetes", "AWS"]
}

prompt = f"""
You are a skill comparison system.

CV TEXT:
{cv_text}

JOB ROLE:
{job_data["role"]}

REQUIRED SKILLS:
{", ".join(job_data["required_skills"])}

PREFERRED SKILLS:
{", ".join(job_data["preferred_skills"])}

Return JSON only:

{{
"matched_skills": [],
"missing_skills": [],
"fit_score": 0,
"feedback": ""
}}
"""

response = requests.post(
    OLLAMA_URL,
    json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
)

result = response.json()["response"]

print(result)