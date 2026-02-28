"""
Exam Evaluator - NLP Grading Engine
Uses TF-IDF vectorization + cosine similarity for semantic matching,
combined with keyword presence scoring and coherence checks.
No external model downloads required.
"""

import re
import math
import string
from typing import List, Optional


# ── Stop words (built-in, no NLTK required) ─────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for", "of", "and",
    "or", "but", "not", "with", "this", "that", "are", "was", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would", "can",
    "could", "should", "may", "might", "shall", "from", "by", "as", "so", "if",
    "then", "than", "there", "their", "they", "we", "our", "us", "you", "your",
    "he", "she", "his", "her", "its", "my", "me", "i", "am", "were", "also",
    "into", "which", "who", "what", "when", "where", "how", "all", "each",
    "both", "more", "most", "other", "some", "such", "no", "only", "same",
    "up", "out", "about", "above", "after", "before", "between", "through",
    "during", "while", "although", "because", "since", "any", "these", "those",
}


def preprocess(text: str) -> List[str]:
    """Tokenise, lowercase, strip punctuation, remove stop words."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def simple_stem(word: str) -> str:
    """Lightweight suffix-stripping stemmer (Porter-inspired)."""
    suffixes = ["ation", "ations", "ing", "ings", "tion", "tions",
                "ness", "ment", "ments", "ers", "ies", "es", "ed", "ly", "s"]
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: len(word) - len(suffix)]
    return word


def stem_tokens(tokens: List[str]) -> List[str]:
    return [simple_stem(t) for t in tokens]


# ── TF-IDF Cosine Similarity ─────────────────────────────────────────────────

def compute_tf(tokens: List[str]) -> dict:
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    total = len(tokens) if tokens else 1
    return {t: count / total for t, count in tf.items()}


def cosine_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute TF cosine similarity between two token lists."""
    if not tokens_a or not tokens_b:
        return 0.0

    tf_a = compute_tf(tokens_a)
    tf_b = compute_tf(tokens_b)

    vocab = set(tf_a) | set(tf_b)

    dot = sum(tf_a.get(w, 0) * tf_b.get(w, 0) for w in vocab)
    mag_a = math.sqrt(sum(v ** 2 for v in tf_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in tf_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Keyword Matching ─────────────────────────────────────────────────────────

def keyword_match_score(student_answer: str, keywords: List[str]) -> tuple[float, List[str], List[str]]:
    """
    Returns (score 0-1, matched keywords, missed keywords).
    Performs stemmed partial matching.
    """
    if not keywords:
        return 1.0, [], []

    student_tokens = set(stem_tokens(preprocess(student_answer)))
    matched, missed = [], []

    for kw in keywords:
        kw_tokens = set(stem_tokens(preprocess(kw)))
        if not kw_tokens:
            continue
        # Match if ANY stem of the keyword appears in student answer
        if kw_tokens & student_tokens:
            matched.append(kw)
        else:
            missed.append(kw)

    total = len(matched) + len(missed)
    score = len(matched) / total if total > 0 else 1.0
    return score, matched, missed