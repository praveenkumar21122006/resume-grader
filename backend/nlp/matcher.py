import re
from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\+\#\.\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def match_job(resume_text: str, job_description: str, resume_skills: List[str]) -> Dict:
    if not job_description or not job_description.strip():
        return {
            "similarity": None,
            "similarity_percent": None,
            "matched_skills": [],
            "missing_skills": [],
            "jd_skills": [],
            "keyword_coverage": None,
            "verdict": "No job description provided — paste a JD to get match analysis."
        }

    # TF-IDF cosine similarity
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2), max_features=5000)
        tfidf = vectorizer.fit_transform([clean_text(resume_text), clean_text(job_description)])
        cos_sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        similarity_percent = round(float(cos_sim) * 100, 1)
    except Exception as e:
        similarity_percent = 0.0
        cos_sim = 0.0

    # Skill overlap with JD
    # Extract skills mentioned in JD
    from .parser import SKILL_DB
    jd_lower = job_description.lower()
    resume_lower = resume_text.lower()
    jd_skills = []
    for skill in SKILL_DB:
        if len(skill) <= 3:
            if re.search(r"\b" + re.escape(skill) + r"\b", jd_lower):
                jd_skills.append(skill)
        else:
            if skill.lower() in jd_lower:
                jd_skills.append(skill)
    jd_skills = sorted(list(set(jd_skills)))

    matched = [s for s in jd_skills if s.lower() in resume_lower or s.lower() in [x.lower() for x in resume_skills]]
    missing = [s for s in jd_skills if s not in matched]

    coverage = round(len(matched) / len(jd_skills) * 100, 1) if jd_skills else 0

    if similarity_percent >= 70:
        verdict = "Excellent match — your resume aligns strongly with this JD."
    elif similarity_percent >= 50:
        verdict = "Good match — with minor keyword tweaks you can be top percentile."
    elif similarity_percent >= 30:
        verdict = "Moderate match — tailor your resume with missing keywords & relevant projects."
    else:
        verdict = "Low match — significant tailoring recommended for this role."

    return {
        "similarity": float(cos_sim),
        "similarity_percent": similarity_percent,
        "matched_skills": matched,
        "missing_skills": missing,
        "jd_skills": jd_skills,
        "keyword_coverage": coverage,
        "verdict": verdict
    }

def extract_jd_keywords(job_description: str, top_n: int = 15) -> List[str]:
    if not job_description.strip():
        return []
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100, ngram_range=(1,2))
        tfidf = vectorizer.fit_transform([clean_text(job_description)])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf.toarray()[0]
        sorted_idx = scores.argsort()[::-1]
        keywords = [feature_names[i] for i in sorted_idx if scores[i] > 0][:top_n]
        return keywords
    except:
        return []
