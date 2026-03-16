from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
from pathlib import Path
import fitz
import os

from skill_gap_engine import analyze_cv_text_file

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
TEXT_FOLDER = "extracted_text"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEXT_FOLDER, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skill Gap Navigator</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #111827;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 32px 20px 60px;
        }
        .hero {
            background: linear-gradient(135deg, #0f172a, #1d4ed8);
            color: white;
            border-radius: 20px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        .hero h1 {
            margin: 0 0 8px;
            font-size: 32px;
        }
        .hero p {
            margin: 0;
            font-size: 16px;
            opacity: 0.95;
        }
        .card {
            background: white;
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
            margin-bottom: 20px;
        }
        .upload-box {
            border: 2px dashed #cbd5e1;
            border-radius: 16px;
            padding: 22px;
            background: #f8fafc;
        }
        input[type=file] {
            width: 100%;
            margin-bottom: 14px;
        }
        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px 18px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 700;
        }
        button:hover {
            background: #1d4ed8;
        }
        .message {
            margin-top: 14px;
            padding: 12px 14px;
            border-radius: 10px;
            background: #e0f2fe;
            color: #0c4a6e;
            font-weight: 700;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }
        .stat {
            background: white;
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .stat-label {
            color: #64748b;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 800;
        }
        .score-bar-wrap {
            margin-top: 12px;
            background: #e2e8f0;
            border-radius: 999px;
            overflow: hidden;
            height: 12px;
        }
        .score-bar {
            height: 12px;
            background: linear-gradient(90deg, #2563eb, #22c55e);
            border-radius: 999px;
        }
        .section-title {
            margin: 0 0 14px;
            font-size: 20px;
        }
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .tag {
            display: inline-block;
            padding: 10px 12px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 700;
        }
        .tag.good {
            background: #dcfce7;
            color: #166534;
        }
        .tag.bad {
            background: #fee2e2;
            color: #991b1b;
        }
        .tag.neutral {
            background: #e2e8f0;
            color: #334155;
        }
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
        .panel {
            background: white;
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .text-box {
            white-space: pre-wrap;
            line-height: 1.6;
            color: #1f2937;
            background: #f8fafc;
            border-radius: 12px;
            padding: 14px;
        }
        .companies {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .company {
            padding: 10px 12px;
            background: #eff6ff;
            color: #1d4ed8;
            border-radius: 999px;
            font-weight: 700;
            font-size: 14px;
        }
        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
            .two-col { grid-template-columns: 1fr; }
            .hero h1 { font-size: 26px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>Skill Gap Navigator</h1>
            <p>Upload a CV and get a clean skill-gap analysis against the job market.</p>
        </div>

        <div class="card">
            <div class="upload-box">
                <form method="POST" enctype="multipart/form-data">
                    <input type="file" name="cv_file" accept=".pdf" required>
                    <button type="submit">Upload and Analyse</button>
                </form>

                {% if message %}
                    <div class="message">{{ message }}</div>
                {% endif %}
            </div>
        </div>

        {% if result %}
            <div class="grid">
                <div class="stat">
                    <div class="stat-label">Detected Field</div>
                    <div class="stat-value">{{ result.detected_field }}</div>
                </div>

                <div class="stat">
                    <div class="stat-label">Estimated Level</div>
                    <div class="stat-value">{{ result.estimated_level }}</div>
                </div>

                <div class="stat">
                    <div class="stat-label">Relevant Jobs Analysed</div>
                    <div class="stat-value">{{ result.relevant_jobs }}</div>
                </div>
            </div>

            <div class="card">
                <h2 class="section-title">Fit Score</h2>
                <div class="stat-value">{{ result.fit_score }}%</div>
                <div class="score-bar-wrap">
                    <div class="score-bar" style="width: {{ result.fit_score }}%;"></div>
                </div>
                <div style="margin-top: 12px; font-weight: 700; color: #334155;">
                    {{ result.alignment_label }}
                </div>
                <div style="margin-top: 10px; color: #475569;">
                    {{ result.similarity_summary }}
                </div>
            </div>

            <div class="panel" style="margin-bottom: 20px;">
                <h2 class="section-title">Companies Actively Hiring</h2>
                <div class="companies">
                    {% for company in result.companies %}
                        <span class="company">{{ company }}</span>
                    {% endfor %}
                </div>
            </div>

            <div class="two-col">
                <div class="panel">
                    <h2 class="section-title">Skills You Already Have</h2>
                    <div class="tag-list">
                        {% for skill in result.matched_skills %}
                            <span class="tag good">{{ skill }}</span>
                        {% endfor %}
                    </div>
                </div>

                <div class="panel">
                    <h2 class="section-title">Skills You Need To Improve</h2>
                    <div class="tag-list">
                        {% for skill in result.missing_skills %}
                            <span class="tag bad">{{ skill }}</span>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div class="panel" style="margin-top: 20px;">
                <h2 class="section-title">What This Means For You</h2>
                <div class="text-box">{{ result.feedback }}</div>
            </div>

            <div class="panel" style="margin-top: 20px;">
                <h2 class="section-title">CV File</h2>
                <span class="tag neutral">{{ result.cv_file }}</span>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

def scan_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def is_valid_text(text):
    if not text:
        return False
    if len(text.strip()) < 200:
        return False
    alpha_chars = sum(c.isalpha() for c in text)
    return alpha_chars > 100

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    result = None

    if request.method == "POST":
        file = request.files.get("cv_file")

        if not file or not file.filename.lower().endswith(".pdf"):
            message = "Please upload a valid PDF file."
            return render_template_string(HTML_PAGE, message=message, result=result)

        safe_name = secure_filename(file.filename)
        base_name = Path(safe_name).stem

        pdf_path = os.path.join(UPLOAD_FOLDER, f"{base_name}.pdf")
        txt_path = os.path.join(TEXT_FOLDER, f"{base_name}.txt")

        file.save(pdf_path)

        extracted_text = scan_pdf(pdf_path)

        if not is_valid_text(extracted_text):
            message = "The uploaded PDF could not be processed properly. Please upload a clearer PDF."
            return render_template_string(HTML_PAGE, message=message, result=result)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        try:
            result = analyze_cv_text_file(txt_path)
            message = "PDF processed and analysed successfully."
        except Exception:
            try:
                result = analyze_cv_text_file(txt_path)
                message = "PDF processed and analysed successfully after retry."
            except Exception:
                try:
                    extracted_text = scan_pdf(pdf_path)

                    if not is_valid_text(extracted_text):
                        message = "The uploaded PDF could not be processed properly. Please upload a different file."
                        return render_template_string(HTML_PAGE, message=message, result=result)

                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(extracted_text)

                    result = analyze_cv_text_file(txt_path)
                    message = "PDF processed successfully after recovery."
                except Exception:
                    message = "Processing failed. Please upload a clearer or different PDF."

    return render_template_string(HTML_PAGE, message=message, result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
