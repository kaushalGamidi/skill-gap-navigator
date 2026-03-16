import pandas as pd
import os

job_folder = "Generated Job Market"

files = [f for f in os.listdir(job_folder) if f.endswith(".xlsx")]

all_jobs = []

for file in files:
    path = os.path.join(job_folder, file)
    df = pd.read_excel(path)
    all_jobs.append(df)

jobs = pd.concat(all_jobs, ignore_index=True)

print("TOTAL JOBS:", len(jobs))
print(jobs.iloc[0])