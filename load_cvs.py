import pandas as pd
import os

cv_folder = "Generated CV'S"

files = [f for f in os.listdir(cv_folder) if f.endswith(".xlsx")]

all_cvs = []

for file in files:
    path = os.path.join(cv_folder, file)
    df = pd.read_excel(path)
    all_cvs.append(df)

cvs = pd.concat(all_cvs, ignore_index=True)

print("TOTAL CVS:", len(cvs))
print(cvs.iloc[0])