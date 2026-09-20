import re
import os
from typing import Dict, List, Optional

# Skill database
SKILL_DB = [
    # Programming
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
    # Web
    "html", "css", "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask", "spring", "fastapi",
    # Data / AI
    "machine learning", "deep learning", "nlp", "computer vision", "data analysis", "data science", "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "keras", "spark", "hadoop",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "elasticsearch", "dynamodb",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "linux", "ci/cd", "terraform", "ansible",
    # Other
    "agile", "scrum", "rest api", "graphql", "microservices", "oop", "system design", "data structures", "algorithms",
    "excel", "tableau", "power bi", "figma", "photoshop", "seo", "marketing", "sales", "project management"
]

ACTION_VERBS = [
    "achieved", "developed", "managed", "led", "created", "implemented", "designed", "built", "launched", "improved",
    "increased", "decreased", "optimized", "automated", "delivered", "coordinated", "analyzed", "engineered", "executed",
    "generated", "initiated", "established", "transformed", "streamlined", "resolved", "mentored", "collaborated", "negotiated",
    "presented", "researched", "supervised", "trained", "architected", "deployed", "scaled", "integrated", "migrated"
]

SECTION_PATTERNS = {
    "contact": r"(contact|phone|email)",
    "summary": r"(summary|objective|profile|about me)",
    "experience": r"(experience|employment|work history|professional experience)",
    "education": r"(education|academic|qualification|university|college|degree)",
    "skills": r"(skills|technologies|tech stack|expertise|competencies)",
    "projects": r"(projects|portfolio)",
    "certifications": r"(certifications|certificates|licenses)",
    "achievements": r"(achievements|awards|honors|accomplishments)"
}

def extract_text_from_pdf(file_path: str) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        return f""

def extract_text_from_docx(file_path: str) -> str:
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return ""

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        # try as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except:
            return ""

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    phone = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin = re.search(r"(linkedin\.com\/in\/[^\s]+)", text, re.I)
    github = re.search(r"(github\.com\/[^\s]+)", text, re.I)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
    }

def extract_sections(text: str) -> Dict[str, bool]:
    lower = text.lower()
    result = {}
    for sec, pattern in SECTION_PATTERNS.items():
        result[sec] = bool(re.search(pattern, lower))
    return result

def extract_skills(text: str) -> List[str]:
    lower = text.lower()
    found = []
    for skill in SKILL_DB:
        # word boundary for short skills, substring for phrases
        if len(skill) <= 3:
            if re.search(r"\b" + re.escape(skill) + r"\b", lower):
                found.append(skill)
        else:
            if skill.lower() in lower:
                found.append(skill)
    return sorted(list(set(found)))

def extract_experience_years(text: str) -> Optional[float]:
    # Look for "X years" patterns
    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", text.lower())
    if matches:
        try:
            years = [float(m) for m in matches]
            # Heuristic: take max as likely total experience, but filter unrealistic >50
            years = [y for y in years if y <= 50]
            return max(years) if years else None
        except:
            pass
    # Fallback: count date ranges like 2018 - 2022, 2019 - Present
    date_ranges = re.findall(r"(19|20)\d{2}\s*[-–—to]+\s*((?:19|20)\d{2}|present|current|now)", text, re.I)
    if date_ranges:
        return float(len(date_ranges) * 1.5)  # rough estimate ~1.5y per role avg if no explicit years
    return None

def count_action_verbs(text: str) -> int:
    lower = text.lower()
    count = 0
    for verb in ACTION_VERBS:
        count += len(re.findall(r"\b" + re.escape(verb) + r"\b", lower))
    return count

def count_quantifiable(text: str) -> int:
    # % , $ , numbers with + , "increased by X%" etc
    patterns = [
        r"\d+%",
        r"\$\s?\d+",
        r"\b\d+\s*(?:million|billion|k)\b",
        r"\b(?:increased|decreased|improved|reduced|grew|saved).{0,20}\d+",
    ]
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, text, re.I))
    # also count bullet points with numbers
    total += len(re.findall(r"\b\d+x\b", text, re.I))
    return total

def text_stats(text: str) -> Dict:
    words = text.split()
    bullets = len(re.findall(r"[\n•\-\*]\s*[A-Z]", text)) + text.count("•")
    # count bullet-like lines
    bullet_lines = len([l for l in text.split("\n") if l.strip().startswith(("•", "-", "*", "·"))])
    sentences = len(re.findall(r"[.!?]+", text))
    return {
        "word_count": len(words),
        "char_count": len(text),
        "bullet_count": max(bullets, bullet_lines),
        "sentence_count": sentences,
        "avg_words_per_sentence": len(words) / max(sentences, 1)
    }

def parse_resume(file_path: str) -> Dict:
    text = extract_text(file_path)
    if not text.strip():
        text = ""
    return {
        "raw_text": text,
        "contact": extract_contact_info(text),
        "sections": extract_sections(text),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "action_verb_count": count_action_verbs(text),
        "quantifiable_count": count_quantifiable(text),
        "stats": text_stats(text),
    }

def parse_text(text: str) -> Dict:
    return {
        "raw_text": text,
        "contact": extract_contact_info(text),
        "sections": extract_sections(text),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "action_verb_count": count_action_verbs(text),
        "quantifiable_count": count_quantifiable(text),
        "stats": text_stats(text),
    }
