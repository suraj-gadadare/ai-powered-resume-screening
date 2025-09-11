from sentence_transformers import SentenceTransformer, util
import re
import os

# Load compact, fast model suitable for Streamlit Cloud
_model_name = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
_model = SentenceTransformer(_model_name)

def compute_match_score(resume_text: str, jd_text: str) -> float:
    """Return cosine similarity * 100 between resume and JD."""
    if not resume_text.strip() or not jd_text.strip():
        return 0.0
    emb1 = _model.encode(resume_text, convert_to_tensor=True, normalize_embeddings=True)
    emb2 = _model.encode(jd_text, convert_to_tensor=True, normalize_embeddings=True)
    sim = util.cos_sim(emb1, emb2).item()
    return round(max(0.0, min(1.0, float(sim))) * 100, 2)

def _load_skill_bank() -> list:
    skills_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "skills_list.txt")
    skills = []
    try:
        with open(skills_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip().lower()
                if s and not s.startswith("#"):
                    skills.append(s)
    except FileNotFoundError:
        skills = ["python","java","c++","sql","aws","azure","gcp","docker","kubernetes",
                  "machine learning","deep learning","nlp","computer vision","pandas",
                  "numpy","scikit-learn","pytorch","tensorflow","django","flask",
                  "react","node","excel","power bi","tableau","communication","leadership"]
    return list(dict.fromkeys(skills))

_SKILL_BANK = _load_skill_bank()

def extract_skills(text: str) -> list:
    """Return unique skills present in text based on a curated bank."""
    t = text.lower()
    found = []
    for skill in _SKILL_BANK:
        # word boundary for single tokens; allow spaces for multi-words
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, t):
            found.append(skill)
    # Keep original order but unique
    seen, out = set(), []
    for s in found:
        if s not in seen:
            out.append(s); seen.add(s)
    return out

def summarize_candidate(name: str, years: int, top_skills: list, score: float) -> str:
    parts = []
    if years:
        parts.append(f"{years} yrs exp")
    if top_skills:
        parts.append("skills: " + ", ".join(top_skills))
    parts.append(f"match {score}%")
    return f"{name} — " + " • ".join(parts)