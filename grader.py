"""
Exam Evaluator — NLP Grading Engine
Pure Python (stdlib). No model downloads. Deployable anywhere.

Edge cases handled:
  - Short model answers (e.g. "hospital"): coherence threshold scales to model length
  - Exact / near-exact match: always gives full marks
  - Empty student answer: always 0
"""

import re
import math
from typing import List, Tuple

STOP_WORDS = {
    "a","an","the","is","it","in","on","at","to","for","of","and","or","but",
    "not","with","this","that","are","was","be","been","being","have","has",
    "had","do","does","did","will","would","can","could","should","may","might",
    "shall","from","by","as","so","if","then","than","there","their","they",
    "we","our","us","you","your","he","she","his","her","its","my","me","i",
    "am","were","also","into","which","who","what","when","where","how","all",
    "each","both","more","most","other","some","such","no","only","same","up",
    "out","about","above","after","before","between","through","during","while",
    "although","because","since","any","these","those",
}

def preprocess(text: str) -> List[str]:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

def simple_stem(word: str) -> str:
    for suffix in ["ation","ations","ing","ings","tion","tions","ness",
                   "ment","ments","ers","ies","es","ed","ly","s"]:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word

def stem_tokens(tokens: List[str]) -> List[str]:
    return [simple_stem(t) for t in tokens]

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip().translate(
        str.maketrans("", "", ".,!?;:'\"")
    ))

def _tf(tokens):
    d = {}
    for t in tokens:
        d[t] = d.get(t, 0) + 1
    n = len(tokens) or 1
    return {t: c / n for t, c in d.items()}

def cosine_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    tfa, tfb = _tf(tokens_a), _tf(tokens_b)
    vocab = set(tfa) | set(tfb)
    dot = sum(tfa.get(w, 0) * tfb.get(w, 0) for w in vocab)
    ma = math.sqrt(sum(v**2 for v in tfa.values()))
    mb = math.sqrt(sum(v**2 for v in tfb.values()))
    if ma == 0 or mb == 0:
        return 0.0
    return dot / (ma * mb)

def keyword_score(student: str, keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    if not keywords:
        return 1.0, [], []
    student_stems = set(stem_tokens(preprocess(student)))
    student_raw   = set(normalize(student).split())
    matched, missed = [], []
    for kw in keywords:
        kw_stems = set(stem_tokens(preprocess(kw)))
        kw_raw   = set(normalize(kw).split())
        if (kw_stems and (kw_stems & student_stems)) or (kw_raw and (kw_raw & student_raw)):
            matched.append(kw)
        else:
            missed.append(kw)
    total = len(matched) + len(missed)
    return (len(matched) / total if total else 1.0), matched, missed

def coherence_score(student: str, model: str, teacher_min_words: int = 15) -> float:
    """Length-aware coherence: never penalises concise answers when model answer is also concise."""
    student_len = len([w for w in student.split() if w.strip()])
    model_len   = len([w for w in model.split()   if w.strip()])
    # Effective minimum = never more than model answer length
    effective_min = min(teacher_min_words, max(model_len, 1))
    if student_len == 0:
        return 0.0
    if student_len >= effective_min:
        return 1.0
    return round(student_len / effective_min, 2)

def overlap_ratio(student: str, model: str) -> float:
    s_tokens = set(stem_tokens(preprocess(student)))
    m_tokens = set(stem_tokens(preprocess(model)))
    if not m_tokens:
        return 1.0
    if not s_tokens:
        return 0.0
    return len(s_tokens & m_tokens) / len(m_tokens)

def is_exact_match(student: str, model: str) -> bool:
    return normalize(student) == normalize(model)

def generate_feedback(sim, kw_sc, coh, missed_kw, final_pct, exact=False):
    if exact:
        return "✅ Perfect answer! Your response matches the expected answer exactly."
    parts = []
    if final_pct >= 0.90:
        parts.append("✅ Excellent answer! You addressed all key points effectively.")
    elif final_pct >= 0.70:
        parts.append("👍 Good answer. You covered the main concepts well.")
    elif final_pct >= 0.45:
        parts.append("⚠️ Partial credit. Your answer is relevant but could be more complete.")
    else:
        parts.append("❌ Your answer does not sufficiently address the question.")
    if sim < 0.30:
        parts.append("Your response seems off-topic compared to the expected answer.")
    elif sim < 0.50:
        parts.append("The core concept is partially addressed but could be more precise.")
    if missed_kw:
        kw_list = ", ".join(f'"{k}"' for k in missed_kw[:4])
        parts.append(f"Missing key concept(s): {kw_list}.")
    if coh < 0.5:
        parts.append("Your answer is too brief — please elaborate.")
    elif coh < 1.0:
        parts.append("Consider expanding your answer with more detail.")
    return " ".join(parts)

def grade_answer(student_answer: str, model_answer: str,
                 keywords: List[str], max_marks: float,
                 min_words: int = 15,
                 weights: Tuple[float,float,float] = (0.50, 0.30, 0.20)) -> dict:

    w_sem, w_kw, w_coh = weights

    if not student_answer.strip() or student_answer.strip() == "(no answer)":
        return {
            "score": 0.0, "max_marks": max_marks, "percentage": 0.0,
            "semantic_similarity": 0.0, "keyword_score": 0.0, "coherence_score": 0.0,
            "matched_keywords": [], "missed_keywords": keywords,
            "feedback": "❌ No answer was provided.",
        }

    exact = is_exact_match(student_answer, model_answer)
    if exact:
        return {
            "score": max_marks, "max_marks": max_marks, "percentage": 100.0,
            "semantic_similarity": 1.0, "keyword_score": 1.0, "coherence_score": 1.0,
            "matched_keywords": keywords, "missed_keywords": [],
            "feedback": "✅ Perfect answer! Your response matches the expected answer exactly.",
        }

    sa_tokens = stem_tokens(preprocess(student_answer))
    ma_tokens = stem_tokens(preprocess(model_answer))
    sim = cosine_similarity(sa_tokens, ma_tokens)
    ov  = overlap_ratio(student_answer, model_answer)
    sim = max(sim, ov * 0.95)

    kw_sc, matched_kw, missed_kw = keyword_score(student_answer, keywords)
    coh = coherence_score(student_answer, model_answer, min_words)

    final_pct = min((sim * w_sem) + (kw_sc * w_kw) + (coh * w_coh), 1.0)
    score = round(final_pct * max_marks, 2)
    feedback = generate_feedback(sim, kw_sc, coh, missed_kw, final_pct, exact)

    return {
        "score": score, "max_marks": max_marks,
        "percentage": round(final_pct * 100, 1),
        "semantic_similarity": round(sim, 3),
        "keyword_score": round(kw_sc, 3),
        "coherence_score": round(coh, 3),
        "matched_keywords": matched_kw,
        "missed_keywords": missed_kw,
        "feedback": feedback,
    }
