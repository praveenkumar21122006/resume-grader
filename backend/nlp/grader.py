from typing import Dict, List
import re

def grade_resume(parsed: Dict, job_description: str = "") -> Dict:
    """
    Returns detailed grading with scores 0-100
    """
    scores = {}
    feedback = []
    suggestions = []

    text = parsed["raw_text"]
    sections = parsed["sections"]
    skills = parsed["skills"]
    stats = parsed["stats"]
    contact = parsed["contact"]
    action_verbs = parsed["action_verb_count"]
    quant = parsed["quantifiable_count"]
    wc = stats["word_count"]

    # 1. Content Completeness (25 points)
    completeness_score = 0
    required_sections = ["experience", "education", "skills"]
    optional_sections = ["summary", "projects", "certifications", "achievements"]
    # required = 15 points
    for sec in required_sections:
        if sections.get(sec):
            completeness_score += 5
        else:
            suggestions.append(f"Add a clear '{sec.title()}' section with relevant details.")
    # optional = up to 6 points
    optional_found = sum(1 for s in optional_sections if sections.get(s))
    completeness_score += min(optional_found * 2, 6)
    # contact = 4 points
    if contact["email"]:
        completeness_score += 2
    else:
        suggestions.append("Add a professional email address at the top.")
    if contact["phone"]:
        completeness_score += 1
    else:
        suggestions.append("Include a phone number for recruiter contact.")
    if contact["linkedin"] or contact["github"]:
        completeness_score += 1
    else:
        suggestions.append("Add LinkedIn / GitHub profile links to boost credibility.")
    
    completeness_score = min(completeness_score, 25)
    scores["completeness"] = completeness_score

    # 2. Formatting & Structure (15 points)
    fmt_score = 10
    if wc < 250:
        fmt_score -= 5
        feedback.append("Resume is too short (<250 words) — expand with more impact and details.")
        suggestions.append("Aim for 450-800 words (1-2 pages) with concise bullet points.")
    elif wc > 1000:
        fmt_score -= 3
        feedback.append("Resume is very long (>1000 words) — recruiters prefer 1-2 pages.")
        suggestions.append("Trim to 1 page (junior) or 2 pages (senior) — remove redundant details.")
    elif 450 <= wc <= 800:
        fmt_score += 2

    if stats["bullet_count"] >= 5:
        fmt_score += 3
    elif stats["bullet_count"] < 3:
        suggestions.append("Use bullet points (•) for experience & achievements — improves readability & ATS parsing.")
        fmt_score -= 2

    # Check for section headings count
    sec_count = sum(1 for v in sections.values() if v)
    if sec_count >= 5:
        fmt_score += 1
    elif sec_count < 3:
        fmt_score -= 2

    fmt_score = max(0, min(fmt_score, 15))
    scores["formatting"] = fmt_score

    # 3. Skills & Keywords (20 points)
    skill_score = 0
    num_skills = len(skills)
    if num_skills >= 12:
        skill_score = 20
    elif num_skills >= 8:
        skill_score = 16
    elif num_skills >= 5:
        skill_score = 12
    elif num_skills >= 3:
        skill_score = 8
    else:
        skill_score = 4
        suggestions.append("List at least 8-12 relevant technical & soft skills (group by category).")
    
    if num_skills < 8:
        feedback.append(f"Only {num_skills} skills detected — add more industry-relevant keywords.")
    
    scores["skills"] = skill_score

    # 4. Experience & Impact (20 points)
    exp_score = 0
    # action verbs 8 pts
    if action_verbs >= 10:
        exp_score += 8
    elif action_verbs >= 5:
        exp_score += 5
    elif action_verbs >= 2:
        exp_score += 3
    else:
        suggestions.append("Start bullet points with strong action verbs: Achieved, Developed, Led, Improved, etc.")
    
    if action_verbs < 5:
        feedback.append(f"Only {action_verbs} strong action verbs found — use more to show impact.")

    # quantifiable 7 pts
    if quant >= 5:
        exp_score += 7
    elif quant >= 3:
        exp_score += 5
    elif quant >= 1:
        exp_score += 3
    else:
        suggestions.append("Quantify achievements with numbers: 'Increased sales by 30%', 'Reduced latency by 200ms', etc.")
        feedback.append("No quantifiable achievements found — numbers make impact credible.")

    # experience years / content depth 5 pts
    if parsed["experience_years"] is not None:
        exp_score += 3
    # if experience section exists
    if sections.get("experience"):
        exp_score += 2
    else:
        exp_score = max(exp_score - 2, 0)

    exp_score = min(exp_score, 20)
    scores["experience"] = exp_score

    # 5. Language & Grammar (10 points)
    lang_score = 8  # base
    # heuristic: avg words per sentence ideal 12-20
    avg = stats["avg_words_per_sentence"]
    if avg > 28:
        lang_score -= 2
        suggestions.append("Shorten long sentences (avg >28 words) — keep them crisp and readable.")
    elif avg < 8:
        lang_score -= 1

    # Check for excessive personal pronouns (I, me)
    pronouns = len(re.findall(r"\b(I|me|my|mine)\b", text))
    if pronouns > 10:
        lang_score -= 2
        suggestions.append("Avoid first-person pronouns ('I', 'my') — use implicit subject: 'Developed X' not 'I developed X'.")

    # Check for spelling-ish: repeated words, double spaces, etc (simple)
    if "  " in text:
        lang_score -= 1

    lang_score = max(0, min(lang_score, 10))
    scores["language"] = lang_score

    # 6. ATS Compatibility (10 points)
    ats_score = 10
    # Check for problematic patterns
    if len(re.findall(r"[^\x00-\x7F]", text)) > 20:  # many non-ascii => possible icons/images
        ats_score -= 2
        suggestions.append("Avoid excessive icons, emojis, or special characters — they can break ATS parsing.")
    if wc < 150:
        ats_score -= 3
    # Need simple headers; if skills section missing ATS suffers
    if not sections.get("skills"):
        ats_score -= 3
    if not contact["email"]:
        ats_score -= 2

    ats_score = max(0, min(ats_score, 10))
    scores["ats"] = ats_score

    total = sum(scores.values())
    # Cap at 100
    total = min(total, 100)

    # Grade letter
    if total >= 90:
        grade = "A+"
        level = "Excellent"
        color = "#10b981"
    elif total >= 80:
        grade = "A"
        level = "Strong"
        color = "#22c55e"
    elif total >= 70:
        grade = "B"
        level = "Good"
        color = "#84cc16"
    elif total >= 60:
        grade = "C"
        level = "Average"
        color = "#eab308"
    elif total >= 50:
        grade = "D"
        level = "Below Average"
        color = "#f97316"
    else:
        grade = "F"
        level = "Needs Improvement"
        color = "#ef4444"

    # Deduplicate suggestions, keep top 7
    seen = set()
    uniq_suggestions = []
    for s in suggestions:
        if s not in seen:
            uniq_suggestions.append(s)
            seen.add(s)
    suggestions = uniq_suggestions[:7]
    if not suggestions and total < 85:
        suggestions.append("Great job! Minor tweaks: tailor keywords to each job description for ATS boost.")

    return {
        "total": total,
        "grade": grade,
        "level": level,
        "color": color,
        "breakdown": {
            "completeness": {"score": scores["completeness"], "max": 25, "label": "Content Completeness"},
            "formatting": {"score": scores["formatting"], "max": 15, "label": "Formatting & Structure"},
            "skills": {"score": scores["skills"], "max": 20, "label": "Skills & Keywords"},
            "experience": {"score": scores["experience"], "max": 20, "label": "Experience & Impact"},
            "language": {"score": scores["language"], "max": 10, "label": "Language & Clarity"},
            "ats": {"score": scores["ats"], "max": 10, "label": "ATS Compatibility"},
        },
        "feedback": feedback,
        "suggestions": suggestions,
        "stats": {
            "words": wc,
            "skills_found": num_skills,
            "action_verbs": action_verbs,
            "quantifiable": quant,
            "sections_found": sec_count
        }
    }
