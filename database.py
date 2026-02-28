"""
Lightweight JSON-based persistence layer.
Uses st.session_state as primary store (survives reruns within a session).
JSON files provide cross-session persistence on local deployments.
On Streamlit Cloud, session_state is the source of truth.
"""

import json
import os
import uuid
import hashlib
import time
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
EXAMS_FILE = DATA_DIR / "exams.json"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"


def _load(path: Path) -> dict:
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ── USERS ─────────────────────────────────────────────────────────────────────
def get_users() -> dict:
    return _load(USERS_FILE)


def create_user(name: str, email: str, password: str, role: str) -> Optional[dict]:
    users = get_users()
    if email in users:
        return None  # already exists
    uid = str(uuid.uuid4())[:8]
    users[email] = {
        "id": uid, "name": name, "email": email,
        "password": hash_password(password),
        "role": role,  # "teacher" or "student"
        "created_at": time.time(),
    }
    _save(USERS_FILE, users)
    return users[email]


def authenticate(email: str, password: str) -> Optional[dict]:
    users = get_users()
    user = users.get(email)
    if user and user["password"] == hash_password(password):
        return user
    return None


# ── EXAMS ─────────────────────────────────────────────────────────────────────
def get_exams() -> dict:
    return _load(EXAMS_FILE)


def create_exam(teacher_id: str, title: str, subject: str,
                questions: list, duration_minutes: int) -> dict:
    exams = get_exams()
    eid = str(uuid.uuid4())[:6].upper()
    exams[eid] = {
        "id": eid,
        "teacher_id": teacher_id,
        "title": title,
        "subject": subject,
        "questions": questions,      # list of {text, model_answer, keywords, max_marks, min_words}
        "duration_minutes": duration_minutes,
        "created_at": time.time(),
        "published": True,
    }
    _save(EXAMS_FILE, exams)
    return exams[eid]


def get_exam(exam_id: str) -> Optional[dict]:
    return get_exams().get(exam_id.upper())


def get_teacher_exams(teacher_id: str) -> list:
    return [e for e in get_exams().values() if e["teacher_id"] == teacher_id]


def update_exam(exam_id: str, data: dict):
    exams = get_exams()
    if exam_id in exams:
        exams[exam_id].update(data)
        _save(EXAMS_FILE, exams)


# ── SUBMISSIONS ───────────────────────────────────────────────────────────────
def get_submissions() -> dict:
    return _load(SUBMISSIONS_FILE)


def save_submission(exam_id: str, student_id: str, student_name: str,
                    results: list, total_score: float, total_marks: float) -> dict:
    submissions = get_submissions()
    sid = str(uuid.uuid4())[:8]
    submissions[sid] = {
        "id": sid,
        "exam_id": exam_id,
        "student_id": student_id,
        "student_name": student_name,
        "results": results,
        "total_score": total_score,
        "total_marks": total_marks,
        "percentage": round((total_score / total_marks * 100) if total_marks else 0, 1),
        "submitted_at": time.time(),
    }
    _save(SUBMISSIONS_FILE, submissions)
    return submissions[sid]


def get_exam_submissions(exam_id: str) -> list:
    return [s for s in get_submissions().values() if s["exam_id"] == exam_id]


def get_student_submissions(student_id: str) -> list:
    return [s for s in get_submissions().values() if s["student_id"] == student_id]


def get_submission(sid: str) -> Optional[dict]:
    return get_submissions().get(sid)


def update_submission_score(sid: str, q_index: int, new_score: float):
    """Allow teacher to override a question score."""
    submissions = get_submissions()
    if sid not in submissions:
        return
    sub = submissions[sid]
    sub["results"][q_index]["score"] = new_score
    sub["results"][q_index]["overridden"] = True
    # Recalculate total
    sub["total_score"] = sum(r["score"] for r in sub["results"])
    sub["percentage"] = round(
        (sub["total_score"] / sub["total_marks"] * 100) if sub["total_marks"] else 0, 1
    )
    _save(SUBMISSIONS_FILE, submissions)


def has_student_submitted(exam_id: str, student_id: str) -> bool:
    return any(
        s["exam_id"] == exam_id and s["student_id"] == student_id
        for s in get_submissions().values()
    )
