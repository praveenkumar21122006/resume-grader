# ResumeGrade — Online Resume Grading Portal with NLP

[![Deploy with Render](https://img.shields.io/badge/Deploy-Render-46e3b0)](https://render.com) [![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org)

Instant, ATS-aware resume scoring (0–100) with actionable feedback. Upload PDF/DOCX/TXT or paste text, optionally paste a Job Description to get **JD match %** and **missing keywords** — powered by NLP (TF-IDF + skill NER).

Live Demo: _push to enable — see Deploy section below_

## Features
- **Text extraction**: PyPDF2 (PDF), python-docx (DOCX), plain text
- **NLP parsing**: contact extraction (email/phone/LinkedIn), section detection, skill NER (50+ skills), experience years, action verbs, quantifiable achievements
- **6-dimension scoring (100 pts)**: Content Completeness 25, Skills 20, Experience & Impact 20, Formatting 15, Language 10, ATS 10 → Grade A+ to F
- **JD Matching**: TF-IDF (1-2 grams) cosine similarity + skill overlap / missing-keyword analysis + top JD keywords
- **Frontend**: Drag-and-drop, paste, live results with ring score, breakdown bars, chips, and suggestions
- **Backend**: Flask + Flask-CORS, REST API

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python backend/app.py        # or: gunicorn wsgi:app
# open http://localhost:5000
```

### API

- `GET /api/health` — health check
- `POST /api/grade` — multipart `file` + optional `job_description` / `text`
- `POST /api/grade-text` — JSON `{ "text": "...", "job_description": "..." }`

Response:
```json
{
  "grading": { "total": 82, "grade": "A", "level": "Strong", "breakdown": {...}, "suggestions": [...] },
  "matching": { "similarity_percent": 64.2, "matched_skills": [...], "missing_skills": [...], "verdict": "..." },
  "parsed": { "skills": [...], "contact": {...}, "sections": {...}, "stats": {...} }
}
```

## Scoring Logic (`backend/nlp/grader.py:1`)
- Completeness: required sections (Experience/Education/Skills) + optional + contact
- Formatting: word count (ideal 450-800), bullet count, section count
- Skills: count of detected skills from curated DB
- Experience: action verbs + quantifiable metrics + years
- Language: sentence length & pronoun checks
- ATS: special chars, missing skills/email penalties

## JD Matcher (`backend/nlp/matcher.py:1`)
TF-IDF vectorizer (english stopwords, 1-2 grams, 5000 features) → cosine similarity → matched/missing skills vs `SKILL_DB`.

## Project Structure
```
resume-grading/
├── backend/
│   ├── app.py
│   └── nlp/{parser,grader,matcher}.py
├── frontend/{index.html, css/style.css, js/app.js}
├── uploads/
├── wsgi.py
├── Procfile
├── render.yaml
├── Dockerfile
└── requirements.txt
```

## Deploy

**Render (recommended, free):**
1. Fork this repo → Render Dashboard → New Web Service → Connect repo
2. Build: `pip install -r requirements.txt` | Start: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
3. Deploy — live in ~2 min.

**Docker:**
```bash
docker build -t resume-grader .
docker run -p 5000:5000 resume-grader
```

**Heroku / Railway / Fly.io:** uses `Procfile` (`web: gunicorn wsgi:app ...`).

## Notes
- Resumes are processed via temp files and not persisted.
- Add `spacy` model (`python -m spacy download en_core_web_sm`) if you want to extend parser with NER.

## License
MIT — see [LICENSE](LICENSE)
