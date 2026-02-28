"""
Exam Evaluator — NLP Grading Engine
Pure Python (stdlib + numpy). No model downloads. Deployable anywhere.

Grading formula:
  Final Score = MaxMarks × [Semantic(0.50) + Keyword(0.30) + Coherence(0.20)]
"""

import re
import math
import string
from typing import List, Tuple

# ── Stop words ───────────────────────────────────────────────────────────────
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
    text = text.lower()
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

# ── TF-IDF Cosine Similarity ─────────────────────────────────────────────────
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

# ── Keyword Matching ─────────────────────────────────────────────────────────
def keyword_score(student: str, keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    if not keywords:
        return 1.0, [], []
    student_stems = set(stem_tokens(preprocess(student)))
    matched, missed = [], []
    for kw in keywords:
        kw_stems = set(stem_tokens(preprocess(kw)))
        if kw_stems and (kw_stems & student_stems):
            matched.append(kw)
        else:
            missed.append(kw)
    total = len(matched) + len(missed)
    return (len(matched) / total if total else 1.0), matched, missed

# ── Coherence Check ───────────────────────────────────────────────────────────
def coherence_score(student: str, min_words: int = 15) -> float:
    words = [w for w in student.split() if w.strip()]
    if len(words) < max(5, min_words // 2):
        return 0.0
    if len(words) < min_words:
        return 0.5
    return 1.0

# ── Feedback Generator ────────────────────────────────────────────────────────
def generate_feedback(sim: float, kw_score: float, coh: float,
                      missed_kw: List[str], final_pct: float) -> str:
    parts = []
    if final_pct >= 0.85:
        parts.append("✅ Excellent answer! You addressed all key points effectively.")
    elif final_pct >= 0.65:
        parts.append("👍 Good answer. You covered the main concepts with minor gaps.")
    elif final_pct >= 0.40:
        parts.append("⚠️ Partial credit. Your answer touches on some relevant points but lacks depth.")
    else:
        parts.append("❌ Your answer does not sufficiently address the question.")

    if sim < 0.35:
        parts.append("Your response seems off-topic compared to the expected answer.")
    elif sim < 0.55:
        parts.append("The core concept is partially addressed but could be more precise.")

    if missed_kw:
        kw_list = ", ".join(f'"{k}"' for k in missed_kw[:4])
        parts.append(f"Missing key concept(s): {kw_list}.")

    if coh == 0.0:
        parts.append("Your answer is too brief — please elaborate.")
    elif coh == 0.5:
        parts.append("Consider expanding your answer with more detail.")

    return " ".join(parts)

# ── Main Grader ───────────────────────────────────────────────────────────────
def grade_answer(student_answer: str, model_answer: str,
                 keywords: List[str], max_marks: float,
                 min_words: int = 15,
                 weights: Tuple[float,float,float] = (0.50, 0.30, 0.20)) -> dict:
    """
    Returns a dict with score, breakdown, feedback, and debug info.
    """
    w_sem, w_kw, w_coh = weights

    # Semantic similarity (TF-IDF cosine)
    sa_tokens = stem_tokens(preprocess(student_answer))
    ma_tokens = stem_tokens(preprocess(model_answer))
    sim = cosine_similarity(sa_tokens, ma_tokens)

    # Keyword matching
    kw_sc, matched_kw, missed_kw = keyword_score(student_answer, keywords)

    # Coherence
    coh = coherence_score(student_answer, min_words)

    # Weighted final
    final_pct = (sim * w_sem) + (kw_sc * w_kw) + (coh * w_coh)
    final_pct = min(final_pct, 1.0)
    score = round(final_pct * max_marks, 2)

    feedback = generate_feedback(sim, kw_sc, coh, missed_kw, final_pct)

    return {
        "score": score,
        "max_marks": max_marks,
        "percentage": round(final_pct * 100, 1),
        "semantic_similarity": round(sim, 3),
        "keyword_score": round(kw_sc, 3),
        "coherence_score": round(coh, 3),
        "matched_keywords": matched_kw,
        "missed_keywords": missed_kw,
        "feedback": feedback,
    }
