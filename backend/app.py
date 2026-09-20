import os
import tempfile
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

try:
    from nlp.parser import parse_resume, parse_text
    from nlp.grader import grade_resume
    from nlp.matcher import match_job, extract_jd_keywords
except ImportError:
    from backend.nlp.parser import parse_resume, parse_text
    from backend.nlp.grader import grade_resume
    from backend.nlp.matcher import match_job, extract_jd_keywords

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads')
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError:
    UPLOAD_FOLDER = "/tmp/uploads"
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    except OSError:
        pass
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "service": "Resume Grading Portal NLP"})

@app.route('/api/grade', methods=['POST'])
def grade():
    """
    Form-data: file (pdf/docx/txt), job_description (optional text)
    """
    job_description = request.form.get('job_description', '') or request.json.get('job_description', '') if request.is_json else request.form.get('job_description', '')
    # Also try to get from form JSON fallback
    if not job_description:
        job_description = request.form.get('jd', '')

    file = request.files.get('file')
    text_input = request.form.get('text', '')

    resume_text = ""
    parsed = None
    filename = None

    if file and file.filename:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Unsupported file type {ext}. Allowed: pdf, docx, txt"}), 400
        # Save temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        try:
            parsed = parse_resume(tmp_path)
            resume_text = parsed["raw_text"]
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
        if not resume_text.strip():
            return jsonify({"error": "Could not extract text from file. Try a text-based PDF or DOCX."}), 400
    elif text_input and text_input.strip():
        resume_text = text_input.strip()
        parsed = parse_text(resume_text)
        filename = "pasted_text.txt"
    else:
        return jsonify({"error": "No file or text provided. Upload a resume or paste text."}), 400

    grading = grade_resume(parsed, job_description)
    matching = match_job(resume_text, job_description, parsed["skills"])
    jd_keywords = extract_jd_keywords(job_description) if job_description else []

    response = {
        "filename": filename,
        "grading": grading,
        "matching": matching,
        "jd_keywords": jd_keywords,
        "parsed": {
            "contact": parsed["contact"],
            "skills": parsed["skills"],
            "sections": parsed["sections"],
            "experience_years": parsed["experience_years"],
            "stats": parsed["stats"],
            "preview": resume_text[:2000]  # first 2k chars
        }
    }
    return jsonify(response)

@app.route('/api/grade-text', methods=['POST'])
def grade_text():
    """
    JSON: { "text": "...", "job_description": "..." }
    """
    data = request.get_json(force=True)
    text = data.get('text', '')
    jd = data.get('job_description', '') or data.get('jd', '')
    if not text or not text.strip():
        return jsonify({"error": "Field 'text' is required"}), 400
    parsed = parse_text(text)
    grading = grade_resume(parsed, jd)
    matching = match_job(text, jd, parsed["skills"])
    jd_keywords = extract_jd_keywords(jd) if jd else []
    return jsonify({
        "grading": grading,
        "matching": matching,
        "jd_keywords": jd_keywords,
        "parsed": {
            "contact": parsed["contact"],
            "skills": parsed["skills"],
            "sections": parsed["sections"],
            "experience_years": parsed["experience_years"],
            "stats": parsed["stats"],
            "preview": text[:2000]
        }
    })

# Serve frontend static fallback
@app.route('/<path:path>')
def serve_static(path):
    full = os.path.join(app.static_folder, path)
    if os.path.exists(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
