"""
Teacher Views — Dashboard, Create Exam, Results
"""

import streamlit as st
import time
import json
from database import (
    get_teacher_exams, create_exam, get_exam, get_exam_submissions,
    update_submission_score, update_exam
)


def nav(page):
    st.session_state.page = page
    st.rerun()


# ── TEACHER DASHBOARD ─────────────────────────────────────────────────────────
def page_teacher_dashboard():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">👩‍🏫 Welcome back, {user["name"]}</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#546E7A">Manage your exams and view student results.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("➕ Create New Exam", use_container_width=True):
            # Reset creation state
            for k in list(st.session_state.keys()):
                if k.startswith("q_"):
                    del st.session_state[k]
            st.session_state.pop("num_questions", None)
            nav("create_exam")

    exams = get_teacher_exams(user["id"])

    if not exams:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#90A4AE;">
          <div style="font-size:3rem">📋</div>
          <div style="font-size:1.1rem;margin-top:0.5rem">No exams yet. Create your first exam!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)
    st.markdown(f"**{len(exams)} Exam(s)**")

    for exam in sorted(exams, key=lambda e: e["created_at"], reverse=True):
        subs = get_exam_submissions(exam["id"])
        total_marks = sum(q["max_marks"] for q in exam["questions"])
        avg_pct = (sum(s["percentage"] for s in subs) / len(subs)) if subs else None

        with st.container():
            st.markdown(f"""
            <div class="eval-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1.15rem;color:#1a237e">{exam['title']}</div>
                  <div style="color:#546E7A;font-size:0.9rem">{exam['subject']} &nbsp;|&nbsp; {len(exam['questions'])} questions &nbsp;|&nbsp; {total_marks} marks &nbsp;|&nbsp; {exam['duration_minutes']} min</div>
                </div>
                <div class="exam-code-box" style="font-size:1.1rem;padding:0.5rem 1rem;letter-spacing:3px">{exam['id']}</div>
              </div>
              <div style="margin-top:0.8rem;color:#546E7A;font-size:0.9rem">
                👥 {len(subs)} submission(s)
                {f'&nbsp;|&nbsp; 📊 Avg: <b>{avg_pct:.1f}%</b>' if avg_pct is not None else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📊 View Results", key=f"view_{exam['id']}", use_container_width=True):
                    st.session_state.selected_exam_id = exam["id"]
                    nav("exam_results")
            with c2:
                # Copy exam code helper
                st.code(exam["id"], language=None)


# ── CREATE EXAM ───────────────────────────────────────────────────────────────
def page_create_exam():
    st.markdown('<div class="section-title">📝 Create New Exam</div>', unsafe_allow_html=True)

    if st.button("← Back to Dashboard"):
        nav("teacher_dashboard")

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    with st.form("exam_meta_form"):
        st.markdown("**Exam Details**")
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            title = st.text_input("Exam Title", placeholder="e.g. Data Structures Mid-Term")
        with c2:
            subject = st.text_input("Subject", placeholder="e.g. Computer Science")
        with c3:
            duration = st.number_input("Duration (min)", min_value=5, max_value=180, value=60)

        num_q = st.number_input("Number of Questions", min_value=1, max_value=20, value=3)
        proceed = st.form_submit_button("Set Up Questions →", use_container_width=True)

    if proceed:
        st.session_state.num_questions = int(num_q)
        st.session_state.exam_title = title
        st.session_state.exam_subject = subject
        st.session_state.exam_duration = duration

    if "num_questions" not in st.session_state:
        return

    n = st.session_state.num_questions
    st.markdown(f'<div style="font-family:Syne,sans-serif;font-weight:700;color:#3949AB;font-size:1.1rem;margin-top:1.5rem">Define {n} Question(s)</div>', unsafe_allow_html=True)

    questions = []
    all_filled = True

    for i in range(n):
        with st.expander(f"Question {i+1}", expanded=(i == 0)):
            q_text = st.text_area(f"Question Text", key=f"q_{i}_text",
                                  placeholder="Enter the exam question here...")
            col1, col2 = st.columns([3, 1])
            with col1:
                model_ans = st.text_area(f"Model Answer", key=f"q_{i}_ans",
                                         placeholder="The ideal/expected answer...", height=100)
            with col2:
                marks = st.number_input("Marks", min_value=1, max_value=50, value=10, key=f"q_{i}_marks")
                min_words = st.number_input("Min Words", min_value=0, max_value=200, value=15, key=f"q_{i}_minw",
                                            help="Minimum answer length to avoid coherence penalty")

            kw_raw = st.text_input(f"Keywords (comma-separated)", key=f"q_{i}_kw",
                                   placeholder="e.g. algorithm, complexity, recursion")
            kw_list = [k.strip() for k in kw_raw.split(",") if k.strip()]

            if not q_text or not model_ans:
                all_filled = False

            questions.append({
                "text": q_text,
                "model_answer": model_ans,
                "keywords": kw_list,
                "max_marks": int(marks),
                "min_words": int(min_words),
            })

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Publish Exam", use_container_width=True, type="primary"):
            if not st.session_state.get("exam_title"):
                st.error("Please fill in exam details first.")
            elif not all_filled:
                st.error("Please fill in all questions and model answers.")
            else:
                exam = create_exam(
                    teacher_id=st.session_state.user["id"],
                    title=st.session_state.exam_title,
                    subject=st.session_state.exam_subject,
                    questions=questions,
                    duration_minutes=st.session_state.exam_duration,
                )
                st.session_state.created_exam = exam
                st.success(f"✅ Exam published! Share code: **{exam['id']}**")
                st.markdown(f'<div class="exam-code-box">{exam["id"]}</div>', unsafe_allow_html=True)
                time.sleep(2)
                nav("teacher_dashboard")

    with col2:
        if st.button("← Cancel", use_container_width=True):
            nav("teacher_dashboard")


# ── EXAM RESULTS ──────────────────────────────────────────────────────────────
def page_exam_results():
    exam_id = st.session_state.get("selected_exam_id")
    if not exam_id:
        nav("teacher_dashboard")
        return

    exam = get_exam(exam_id)
    if not exam:
        st.error("Exam not found.")
        nav("teacher_dashboard")
        return

    if st.button("← Back to Dashboard"):
        nav("teacher_dashboard")

    st.markdown(f'<div class="section-title">📊 {exam["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'Code: **{exam["id"]}** &nbsp;|&nbsp; {exam["subject"]} &nbsp;|&nbsp; {len(exam["questions"])} questions &nbsp;|&nbsp; {sum(q["max_marks"] for q in exam["questions"])} total marks', unsafe_allow_html=True)

    subs = get_exam_submissions(exam_id)

    if not subs:
        st.info("No submissions yet. Share the exam code with students.")
        return

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    # Summary metrics
    percentages = [s["percentage"] for s in subs]
    avg = sum(percentages) / len(percentages)
    highest = max(percentages)
    lowest = min(percentages)
    passed = sum(1 for p in percentages if p >= 50)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Submissions", len(subs))
    m2.metric("Average Score", f"{avg:.1f}%")
    m3.metric("Highest Score", f"{highest:.1f}%")
    m4.metric("Pass Rate (≥50%)", f"{passed}/{len(subs)}")

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    # Score distribution bar (simple ASCII-free version)
    buckets = {"0-49%": 0, "50-64%": 0, "65-79%": 0, "80-100%": 0}
    for p in percentages:
        if p < 50: buckets["0-49%"] += 1
        elif p < 65: buckets["50-64%"] += 1
        elif p < 80: buckets["65-79%"] += 1
        else: buckets["80-100%"] += 1

    st.markdown("**Score Distribution**")
    max_b = max(buckets.values()) or 1
    cols = st.columns(len(buckets))
    colors = ["#ef5350", "#FFA726", "#66BB6A", "#42A5F5"]
    for i, (label, count) in enumerate(buckets.items()):
        with cols[i]:
            pct = count / max_b * 100
            st.markdown(f"""
            <div style="text-align:center;">
              <div style="background:#e8eaf6;border-radius:8px;height:80px;display:flex;align-items:flex-end;overflow:hidden;">
                <div style="background:{colors[i]};width:100%;height:{max(5,pct)}%;border-radius:6px;"></div>
              </div>
              <div style="font-size:0.85rem;color:#546E7A;margin-top:4px">{label}</div>
              <div style="font-weight:700;color:#1a237e">{count}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)
    st.markdown("**Student Submissions**")

    for sub in sorted(subs, key=lambda s: s["percentage"], reverse=True):
        pct = sub["percentage"]
        badge = "badge-green" if pct >= 65 else ("badge-yellow" if pct >= 40 else "badge-red")
        emoji = "🟢" if pct >= 65 else ("🟡" if pct >= 40 else "🔴")

        with st.expander(f"{emoji} {sub['student_name']} — {sub['total_score']}/{sub['total_marks']} ({pct}%)"):
            st.markdown(f'<span class="score-badge {badge}">{pct}%</span>', unsafe_allow_html=True)

            for qi, res in enumerate(sub["results"]):
                q = exam["questions"][qi]
                q_score = res["score"]
                q_max = res["max_marks"]
                q_pct = (q_score / q_max * 100) if q_max else 0
                overridden = res.get("overridden", False)

                st.markdown(f"""
                <div style="background:#f8f9ff;border-radius:10px;padding:1rem;margin:0.5rem 0;border-left:4px solid {'#43A047' if q_pct>=65 else ('#FFA726' if q_pct>=40 else '#ef5350')}">
                  <div style="font-weight:600;color:#1a237e">Q{qi+1}: {q['text'][:80]}{'...' if len(q['text'])>80 else ''}</div>
                  <div style="color:#546E7A;font-size:0.85rem;margin:0.3rem 0">Score: <b>{q_score}/{q_max}</b> ({q_pct:.0f}%) {'⚙️ Overridden' if overridden else ''}</div>
                  <div style="color:#37474F;font-size:0.9rem;background:white;border-radius:6px;padding:0.5rem;margin-top:0.4rem"><i>Student:</i> {res.get('student_answer','')[:200]}</div>
                  <div style="color:#546E7A;font-size:0.85rem;margin-top:0.4rem">💬 {res.get('feedback','')}</div>
                  <div style="font-size:0.8rem;color:#78909C;margin-top:0.3rem">
                    Semantic: {res.get('semantic_similarity',0):.2f} | Keywords: {res.get('keyword_score',0):.2f} | Coherence: {res.get('coherence_score',0):.2f}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Score override
                new_score = st.number_input(
                    f"Override score (Q{qi+1})",
                    min_value=0.0, max_value=float(q_max),
                    value=float(q_score), step=0.5,
                    key=f"override_{sub['id']}_{qi}"
                )
                if new_score != q_score:
                    if st.button(f"Apply Override", key=f"apply_{sub['id']}_{qi}"):
                        update_submission_score(sub["id"], qi, new_score)
                        st.success("Score updated!")
                        st.rerun()
