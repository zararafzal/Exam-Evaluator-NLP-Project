"""Teacher Views — Dashboard, Create Exam, Results"""

import streamlit as st
import time
from database import (
    get_teacher_exams, create_exam, get_exam,
    get_exam_submissions, update_submission_score
)

def nav(page):
    st.session_state.page = page
    st.rerun()

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
def page_teacher_dashboard():
    user = st.session_state.user
    st.markdown(f'<div class="page-title">👩‍🏫 My Exams</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">Hello, {user["name"]}. Manage your exams and see student results.</div>', unsafe_allow_html=True)

    if st.button("➕ Create New Exam", type="primary"):
        for k in [k for k in st.session_state if k.startswith("q_") or k == "num_questions"]:
            del st.session_state[k]
        nav("create_exam")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    exams = get_teacher_exams(user["id"])
    if not exams:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;opacity:0.4;">
          <div style="font-size:2.5rem">📋</div>
          <div style="margin-top:0.4rem">No exams yet. Create your first one above.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for exam in sorted(exams, key=lambda e: e["created_at"], reverse=True):
        subs        = get_exam_submissions(exam["id"])
        total_marks = sum(q["max_marks"] for q in exam["questions"])
        avg_pct     = (sum(s["percentage"] for s in subs) / len(subs)) if subs else None

        with st.container():
            c1, c2 = st.columns([3, 1], gap="small")
            with c1:
                st.markdown(f"""
                <div class="card">
                  <div style="font-weight:700; font-size:1.05rem">{exam['title']}</div>
                  <div style="opacity:0.6; font-size:0.85rem; margin-top:0.2rem">
                    {exam['subject']} &nbsp;·&nbsp; {len(exam['questions'])} questions &nbsp;·&nbsp;
                    {total_marks} marks &nbsp;·&nbsp; {exam['duration_minutes']} min
                  </div>
                  <div style="margin-top:0.6rem; display:flex; gap:0.6rem; align-items:center; flex-wrap:wrap;">
                    <span class="code-pill">{exam['id']}</span>
                    <span class="badge badge-blue">👥 {len(subs)} submission(s)</span>
                    {f'<span class="badge badge-green">📊 Avg {avg_pct:.1f}%</span>' if avg_pct is not None else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                if st.button("📊 Results", key=f"res_{exam['id']}", use_container_width=True):
                    st.session_state.selected_exam_id = exam["id"]
                    nav("exam_results")

# ── CREATE EXAM ───────────────────────────────────────────────────────────────
def page_create_exam():
    st.markdown('<div class="page-title">📝 Create New Exam</div>', unsafe_allow_html=True)
    if st.button("← Back"):
        nav("teacher_dashboard")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("**Step 1 — Exam details**")

    with st.form("exam_meta"):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1: title    = st.text_input("Exam Title", placeholder="e.g. Data Structures Mid-Term")
        with c2: subject  = st.text_input("Subject",    placeholder="e.g. Computer Science")
        with c3: duration = st.number_input("Duration (min)", 5, 180, 60)
        num_q = st.number_input("Number of Questions", 1, 20, 3)
        if st.form_submit_button("Continue →", use_container_width=True):
            st.session_state.num_questions  = int(num_q)
            st.session_state.exam_title     = title
            st.session_state.exam_subject   = subject
            st.session_state.exam_duration  = duration

    if "num_questions" not in st.session_state:
        return

    n = st.session_state.num_questions
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(f"**Step 2 — Define {n} question(s)**")
    st.caption("For short/factual answers (e.g. a single word), set Min Words to 0 or 1 so the AI doesn't penalise concise correct answers.")

    questions   = []
    all_filled  = True

    for i in range(n):
        with st.expander(f"Question {i+1}", expanded=True):
            q_text    = st.text_area("Question",     key=f"q_{i}_text", placeholder="Type the question here…")
            model_ans = st.text_area("Model Answer", key=f"q_{i}_ans",  placeholder="The ideal answer (even a single word is fine)…", height=80)
            c1, c2 = st.columns(2)
            with c1: marks     = st.number_input("Marks",     1, 100, 10, key=f"q_{i}_marks")
            with c2: min_words = st.number_input("Min Words", 0, 200,  0, key=f"q_{i}_minw",
                                                 help="0 = no minimum (good for single-word answers)")
            kw_raw  = st.text_input("Keywords (comma-separated, optional)", key=f"q_{i}_kw",
                                     placeholder="e.g. recursion, complexity, algorithm")
            kw_list = [k.strip() for k in kw_raw.split(",") if k.strip()]
            if not q_text or not model_ans:
                all_filled = False
            questions.append({
                "text": q_text, "model_answer": model_ans,
                "keywords": kw_list, "max_marks": int(marks), "min_words": int(min_words),
            })

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Publish Exam", type="primary", use_container_width=True):
            if not st.session_state.get("exam_title"):
                st.error("Fill in exam details first (Step 1).")
            elif not all_filled:
                st.error("Please fill in every question and model answer.")
            else:
                exam = create_exam(
                    teacher_id=st.session_state.user["id"],
                    title=st.session_state.exam_title,
                    subject=st.session_state.exam_subject,
                    questions=questions,
                    duration_minutes=st.session_state.exam_duration,
                )
                st.success(f"✅ Exam published! Share this code with your students:")
                st.markdown(f'<div style="text-align:center;padding:1rem 0"><span class="code-pill" style="font-size:1.6rem;letter-spacing:8px">{exam["id"]}</span></div>', unsafe_allow_html=True)
                time.sleep(2)
                nav("teacher_dashboard")
    with c2:
        if st.button("Cancel", use_container_width=True):
            nav("teacher_dashboard")

# ── EXAM RESULTS ──────────────────────────────────────────────────────────────
def page_exam_results():
    exam_id = st.session_state.get("selected_exam_id")
    if not exam_id:
        nav("teacher_dashboard"); return

    exam = get_exam(exam_id)
    if not exam:
        st.error("Exam not found."); nav("teacher_dashboard"); return

    if st.button("← Back to Dashboard"):
        nav("teacher_dashboard")

    st.markdown(f'<div class="page-title">📊 {exam["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">Code: <b>{exam["id"]}</b> &nbsp;·&nbsp; {exam["subject"]} &nbsp;·&nbsp; {len(exam["questions"])} questions &nbsp;·&nbsp; {sum(q["max_marks"] for q in exam["questions"])} total marks</div>', unsafe_allow_html=True)

    subs = get_exam_submissions(exam_id)
    if not subs:
        st.info("No submissions yet. Share the exam code with students."); return

    percentages = [s["percentage"] for s in subs]
    avg    = sum(percentages) / len(percentages)
    passed = sum(1 for p in percentages if p >= 50)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Submissions", len(subs))
    m2.metric("Average",     f"{avg:.1f}%")
    m3.metric("Highest",     f"{max(percentages):.1f}%")
    m4.metric("Pass Rate",   f"{passed}/{len(subs)}")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("**Individual Results**")

    for sub in sorted(subs, key=lambda s: s["percentage"], reverse=True):
        pct   = sub["percentage"]
        badge = "badge-green" if pct >= 65 else ("badge-yellow" if pct >= 40 else "badge-red")
        emoji = "🟢" if pct >= 65 else ("🟡" if pct >= 40 else "🔴")

        with st.expander(f"{emoji} {sub['student_name']} — {sub['total_score']}/{sub['total_marks']} ({pct}%)"):
            for qi, res in enumerate(sub["results"]):
                q       = exam["questions"][qi]
                q_score = res["score"]
                q_max   = res["max_marks"]
                q_pct   = (q_score / q_max * 100) if q_max else 0

                st.markdown(f"""
                <div class="card" style="border-left: 4px solid {'#16a34a' if q_pct>=65 else ('#b45309' if q_pct>=40 else '#dc2626')}">
                  <div style="font-weight:700">Q{qi+1}: {q['text'][:100]}{'…' if len(q['text'])>100 else ''}</div>
                  <div style="opacity:0.6; font-size:0.85rem; margin:0.3rem 0">
                    Score: <b>{q_score}/{q_max}</b> ({q_pct:.0f}%)
                    {'&nbsp; ⚙️ <i>Overridden</i>' if res.get('overridden') else ''}
                  </div>
                  <div style="font-size:0.9rem; padding:0.5rem; border-radius:8px; background:rgba(128,128,128,0.08); margin-top:0.4rem">
                    <i>Student:</i> {res.get('student_answer','') or '(no answer)'}
                  </div>
                  <div style="font-size:0.85rem; opacity:0.7; margin-top:0.4rem">💬 {res.get('feedback','')}</div>
                  <div style="font-size:0.78rem; opacity:0.5; margin-top:0.2rem">
                    Semantic: {res.get('semantic_similarity',0):.2f} &nbsp;|&nbsp;
                    Keywords: {res.get('keyword_score',0):.2f} &nbsp;|&nbsp;
                    Coherence: {res.get('coherence_score',0):.2f}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                new_score = st.number_input(
                    f"Override score for Q{qi+1}",
                    0.0, float(q_max), float(q_score), 0.5,
                    key=f"ov_{sub['id']}_{qi}"
                )
                if new_score != q_score:
                    if st.button("Apply Override", key=f"ap_{sub['id']}_{qi}"):
                        update_submission_score(sub["id"], qi, new_score)
                        st.success("Score updated!"); st.rerun()
