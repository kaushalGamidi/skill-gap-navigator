# Skill Gap Navigator

Skill Gap Navigator is an AI-powered web application that analyzes a user's CV and compares their skills with job market requirements.

## Features

- Upload CV in PDF format
- Extract text from CV automatically
- Identify skills from CV
- Compare skills with job market datasets
- Generate skill-gap insights
- Provide improvement recommendations

## System Architecture

User CV Upload → PDF Text Extraction → Skill Detection → Job Market Comparison → Skill Gap Analysis → Results Display

## Technologies Used

- Python
- Flask
- NLP techniques
- Azure VM deployment
- HTTPS with Nginx
- GitHub for version control

## Deployment

The system is deployed on an Azure Virtual Machine.

Live system:

https://skillgap-ai.swedencentral.cloudapp.azure.com

## Installation

Clone the repository:

git clone https://github.com/kaushalGamidi/skill-gap-navigator.git

Install dependencies:

pip install -r requirements.txt

Run the application:

python app.py

## Project Purpose

This project helps students understand the gap between their current skills and the skills required in the job market.







Project File Structure
skill-gap-navigator/

Core Application

app.py – Main Flask web application that runs the system and handles CV uploads.

skill_gap_engine.py – Core logic that analyzes skills and calculates the skill gap.

compare_ai.py – AI-based comparison of CV skills with job market skills.

ai_bridge.py – Interface that connects the application with the AI comparison system.

Data Processing

read_cv.py – Extracts text content from uploaded CV PDF files.

load_jobs.py – Loads job market datasets used for skill comparison.

load_cvs.py – Loads generated CV datasets for testing and validation.

Skill Analysis

role_level_matcher.py – Determines role level (e.g., junior, mid, senior) based on skills.

ollama_compare.py – Handles AI model comparison between CV and job requirements.

Testing / Development Versions

app_working.py – Backup or alternative working version of the main application.

skill_gap_engine_working.py – Testing version of the skill gap engine during development.

skill_gap_engine.py.bak – Backup file from earlier development stage.

Datasets and Storage

Generated CV'S/ – Synthetic CV dataset used for testing the system.

Generated Job Market/ – Job market dataset containing role requirements.

uploads/ – Folder where user CV files are temporarily stored.

extracted_text/ – Stores extracted CV text after PDF processing.

Configuration

requirements.txt – Python dependencies required to run the project.

.gitignore – Defines files and folders that should not be tracked by Git.

Deployment Environment

The system is deployed on an Azure Virtual Machine (Linux) where:

The Flask application runs behind Nginx

HTTPS is configured using Let's Encrypt

The application is publicly accessible through:

https://skillgap-ai.swedencentral.cloudapp.azure.com



System Pipeline
CV → NLP → Skill Extraction → Job Dataset → AI Comparison → Gap Result
