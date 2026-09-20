import os
import sys

# Vercel bundles api/ as function dir. Ensure imports work in both local & Vercel.
# Try api/nlp first, then backend/nlp, then root/backend.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND = os.path.join(ROOT, 'backend')
API_DIR = os.path.dirname(__file__)

# Add paths for imports
for p in [API_DIR, BACKEND, ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Import Flask app - try multiple strategies for Vercel compatibility
app = None
try:
    # Strategy 1: import from api/nlp-backed standalone app (copy of backend/app)
    # We create a minimal Flask app here if backend import fails
    from app import app as _app
    app = _app
except Exception as e1:
    try:
        from backend.app import app as _app
        app = _app
    except Exception as e2:
        # Fallback: create app inline using api/nlp modules
        import tempfile
        from flask import Flask, request, jsonify, send_from_directory
        from flask_cors import CORS
        from werkzeug.utils import secure_filename

        # Try api/nlp then backend/nlp
        try:
            from nlp.parser import parse_resume, parse_text
            from nlp.grader import grade_resume
            from nlp.matcher import match_job, extract_jd_keywords
        except ImportError:
            from api.nlp.parser import parse_resume, parse_text
            from api.nlp.grader import grade_resume
            from api.nlp.matcher import match_job, extract_jd_keywords

        FRONTEND_DIR = os.path.abspath(os.path.join(ROOT, 'frontend'))
        # On Vercel, frontend may be bundled via includeFiles - try alternative paths
        if not os.path.exists(FRONTEND_DIR):
            for alt in [os.path.join(API_DIR, '..', 'frontend'), os.path.join(os.getcwd(), 'frontend'), '/vercel/path1/frontend']:
                if os.path.exists(alt):
                    FRONTEND_DIR = os.path.abspath(alt)
                    break

        app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
        CORS(app)
        UPLOAD_FOLDER = os.path.join(ROOT, 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

        @app.route('/')
        def index():
            return send_from_directory(app.static_folder, 'index.html')

        @app.route('/api/health')
        def health():
            return jsonify({"status": "ok", "service": "Resume Grading Portal NLP"})

        @app.route('/api/grade', methods=['POST'])
        def grade():
            job_description = request.form.get('job_description', '') or (request.json.get('job_description', '') if request.is_json else request.form.get('job_description', ''))
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
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name
                try:
                    parsed = parse_resume(tmp_path)
                    resume_text = parsed["raw_text"]
                finally:
                    try: os.unlink(tmp_path)
                    except: pass
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
            response = {"filename": filename, "grading": grading, "matching": matching, "jd_keywords": jd_keywords, "parsed": {"contact": parsed["contact"], "skills": parsed["skills"], "sections": parsed["sections"], "experience_years": parsed["experience_years"], "stats": parsed["stats"], "preview": resume_text[:2000]}}
            return jsonify(response)

        @app.route('/api/grade-text', methods=['POST'])
        def grade_text():
            data = request.get_json(force=True)
            text = data.get('text', '')
            jd = data.get('job_description', '') or data.get('jd', '')
            if not text or not text.strip():
                return jsonify({"error": "Field 'text' is required"}), 400
            parsed = parse_text(text)
            grading = grade_resume(parsed, jd)
            matching = match_job(text, jd, parsed["skills"])
            jd_keywords = extract_jd_keywords(jd) if jd else []
            return jsonify({"grading": grading, "matching": matching, "jd_keywords": jd_keywords, "parsed": {"contact": parsed["contact"], "skills": parsed["skills"], "sections": parsed["sections"], "experience_years": parsed["experience_years"], "stats": parsed["stats"], "preview": text[:2000]}})

        @app.route('/<path:path>')
        def serve_static(path):
            full = os.path.join(app.static_folder, path)
            if os.path.exists(full):
                return send_from_directory(app.static_folder, path)
            return send_from_directory(app.static_folder, 'index.html')

# Vercel expects app
handler = app
