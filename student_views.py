"""
Student Views — Dashboard, Take Exam, My Results
"""

import streamlit as st
import time
from database import (
    get_exam, save_submission, get_student_submissions,
    has_student_submitted, get_submission
)
from grader import grade_answer


def nav(page):
    st.session_state.page = page
    st.rerun()


# ── STUDENT DASHBOARD ─────────────────────────────────────────────────────────
def page_student_dashboard():
    user = st.session_state.user
    st.markdown(f'<div class="section-title">🧑‍🎓 Welcome, {user["name"]}</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#546E7A">Enter an exam code to start, or view your past results.</p>', unsafe_allow_html=True)

    # Join exam
    st.markdown("**Join an Exam**")
    with st.form("join_exam_form"):
        c1, c2 = st.columns([3, 1])
        with c1:
            code = st.text_input("Exam Code", placeholder="e.g. AB12CD", label_visibility="collapsed")
        with c2:
            go = st.form_submit_button("Join →", use_container_width=True)

        if go:
            code = code.strip().upper()
            if not code:
                st.error("Please enter an exam code.")
            else:
                exam = get_exam(code)
                if not exam:
                    st.error("Exam not found. Check the code and try again.")
                elif has_student_submitted(code, user["id"]):
                    st.warning("You have already submitted this exam. View your results below.")
                else:
                    st.session_state.active_exam_id = code
                    st.session_state.student_answers = {}
                    st.session_state.exam_start_time = time.time()
                    nav("take_exam")

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    # Past submissions
    subs = get_student_submissions(user["id"])
    if subs:
        st.markdown(f"**Your Submissions ({len(subs)})**")
        for sub in sorted(subs, key=lambda s: s["submitted_at"], reverse=True):
            pct = sub["percentage"]
            badge = "badge-green" if pct >= 65 else ("badge-yellow" if pct >= 40 else "badge-red")
            emoji = "🟢" if pct >= 65 else ("🟡" if pct >= 40 else "🔴")
            exam = get_exam(sub["exam_id"])
            exam_title = exam["title"] if exam else sub["exam_id"]

            st.markdown(f"""
            <div class="eval-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-family:'Syne',sans-serif;font-weight:700;color:#1a237e">{emoji} {exam_title}</div>
                  <div style="color:#546E7A;font-size:0.9rem">Exam: {sub['exam_id']}</div>
                </div>
                <div>
                  <span class="score-badge {badge}">{sub['total_score']}/{sub['total_marks']} &mdash; {pct}%</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("View Details", key=f"view_sub_{sub['id']}"):
                st.session_state.selected_submission_id = sub["id"]
                nav("my_results")
    else:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#90A4AE;">
          <div style="font-size:3rem">📋</div>
          <div>No submissions yet. Join an exam to get started!</div>
        </div>
        """, unsafe_allow_html=True)


# ── TAKE EXAM ─────────────────────────────────────────────────────────────────
def page_take_exam():
    user = st.session_state.user
    exam_id = st.session_state.get("active_exam_id")
    if not exam_id:
        nav("student_dashboard")
        return

    exam = get_exam(exam_id)
    if not exam:
        st.error("Exam not found.")
        nav("student_dashboard")
        return

    # Timer logic
    start_time = st.session_state.get("exam_start_time", time.time())
    duration_secs = exam["duration_minutes"] * 60
    elapsed = time.time() - start_time
    remaining = max(0, duration_secs - elapsed)
    timed_out = remaining <= 0

    # Header
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        st.markdown(f'<div class="section-title">{exam["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<span style="color:#546E7A">{exam["subject"]}</span>', unsafe_allow_html=True)
    with c2:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        timer_color = "#ef5350" if remaining < 120 else ("#FFA726" if remaining < 300 else "#43A047")
        st.markdown(f"""
        <div style="background:{timer_color}15;border:2px solid {timer_color};border-radius:12px;
                    padding:0.8rem;text-align:center;">
          <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.8rem;color:{timer_color}">
            {mins:02d}:{secs:02d}
          </div>
          <div style="font-size:0.8rem;color:#546E7A">Time Remaining</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        total_marks = sum(q["max_marks"] for q in exam["questions"])
        st.markdown(f"""
        <div style="background:#e8eaf6;border-radius:12px;padding:0.8rem;text-align:center;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1.4rem;color:#3949AB">{len(exam['questions'])}</div>
          <div style="font-size:0.85rem;color:#546E7A">Questions &nbsp;|&nbsp; {total_marks} Marks</div>
        </div>
        """, unsafe_allow_html=True)

    if timed_out:
        st.error("⏰ Time's up! Submitting your answers now...")

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    # Question forms
    if "student_answers" not in st.session_state:
        st.session_state.student_answers = {}

    answers = {}
    for i, q in enumerate(exam["questions"]):
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#e8eaf6 0%,#e3f2fd 100%);
                    border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.5rem;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;color:#1a237e">
            Q{i+1} &nbsp;<span style="font-size:0.85rem;background:#3949AB;color:white;border-radius:6px;padding:2px 8px;">{q['max_marks']} marks</span>
          </div>
          <div style="margin-top:0.4rem;color:#37474F">{q['text']}</div>
        </div>
        """, unsafe_allow_html=True)

        existing = st.session_state.student_answers.get(i, "")
        answer = st.text_area(
            f"Your Answer",
            value=existing,
            key=f"ans_{i}",
            placeholder="Type your answer here...",
            height=120,
            disabled=timed_out,
            label_visibility="collapsed"
        )
        answers[i] = answer
        word_count = len(answer.split()) if answer.strip() else 0
        min_w = q.get("min_words", 15)
        wc_color = "#43A047" if word_count >= min_w else "#FFA726" if word_count > 0 else "#90A4AE"
        st.markdown(f'<div style="font-size:0.8rem;color:{wc_color};text-align:right;margin-top:-0.5rem">{word_count} words (min {min_w})</div>', unsafe_allow_html=True)
        st.markdown("")

    # Auto-collect answers into session state
    if not timed_out:
        st.session_state.student_answers = answers

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        submit_clicked = st.button("🚀 Submit Exam", use_container_width=True, type="primary")
    with col2:
        if st.button("← Cancel", use_container_width=True):
            nav("student_dashboard")

    # Auto submit on timeout
    should_submit = submit_clicked or timed_out

    if should_submit:
        final_answers = st.session_state.student_answers if not timed_out else answers

        with st.spinner("🧠 Grading your answers..."):
            results = []
            total_score = 0
            total_marks = 0

            for i, q in enumerate(exam["questions"]):
                student_ans = final_answers.get(i, "").strip()
                result = grade_answer(
                    student_answer=student_ans if student_ans else "(no answer)",
                    model_answer=q["model_answer"],
                    keywords=q.get("keywords", []),
                    max_marks=q["max_marks"],
                    min_words=q.get("min_words", 15),
                )
                result["question_text"] = q["text"]
                result["student_answer"] = student_ans
                results.append(result)
                total_score += result["score"]
                total_marks += q["max_marks"]

            submission = save_submission(
                exam_id=exam_id,
                student_id=user["id"],
                student_name=user["name"],
                results=results,
                total_score=total_score,
                total_marks=total_marks,
            )

        st.session_state.selected_submission_id = submission["id"]
        st.success("✅ Submitted successfully!")
        time.sleep(1)
        nav("my_results")

    # Auto-refresh timer every 5 seconds if exam is live
    if not timed_out and remaining > 0:
        time.sleep(0)  # yield; Streamlit will re-run on next interaction
        # Show a note about the timer
        st.markdown('<div style="text-align:center;color:#90A4AE;font-size:0.8rem">⏱ Timer shown above — refresh the page to update</div>', unsafe_allow_html=True)


# ── MY RESULTS ─────────────────────────────────────────────────────────────────
def page_my_results():
    sub_id = st.session_state.get("selected_submission_id")
    if not sub_id:
        nav("student_dashboard")
        return

    sub = get_submission(sub_id)
    if not sub:
        st.error("Result not found.")
        nav("student_dashboard")
        return

    exam = get_exam(sub["exam_id"])
    exam_title = exam["title"] if exam else sub["exam_id"]

    if st.button("← Back to Dashboard"):
        nav("student_dashboard")

    pct = sub["percentage"]
    total_score = sub["total_score"]
    total_marks = sub["total_marks"]

    # Grade label
    if pct >= 85:   grade, grade_color = "A — Excellent",  "#2e7d32"
    elif pct >= 70: grade, grade_color = "B — Good",       "#1565c0"
    elif pct >= 55: grade, grade_color = "C — Average",    "#e65100"
    elif pct >= 40: grade, grade_color = "D — Pass",       "#f57f17"
    else:           grade, grade_color = "F — Fail",       "#c62828"

    st.markdown(f'<div class="section-title">📋 {exam_title} — Results</div>', unsafe_allow_html=True)

    # Big score card
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a237e,#3949AB);border-radius:20px;padding:2rem;color:white;text-align:center;margin:1rem 0;">
      <div style="font-family:'Syne',sans-serif;font-size:3.5rem;font-weight:800;line-height:1">{total_score}</div>
      <div style="font-size:1.1rem;opacity:0.8">out of {total_marks} marks</div>
      <div style="margin-top:0.8rem;">
        <div style="background:white;border-radius:20px;height:10px;overflow:hidden;max-width:300px;margin:0 auto;">
          <div style="background:{'#43A047' if pct>=55 else '#ef5350'};height:100%;width:{pct}%;border-radius:20px;"></div>
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;margin-top:0.5rem">{pct}%</div>
        <div style="font-size:1rem;font-weight:600;color:#FFE082">{grade}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Per-question breakdown
    st.markdown("**Question-by-Question Breakdown**")

    for i, res in enumerate(sub["results"]):
        q_score = res["score"]
        q_max = res["max_marks"]
        q_pct = (q_score / q_max * 100) if q_max else 0
        bar_color = "#43A047" if q_pct >= 65 else ("#FFA726" if q_pct >= 40 else "#ef5350")
        overridden = res.get("overridden", False)

        with st.expander(f"Q{i+1}: {res.get('question_text','')[:60]}... — {q_score}/{q_max} ({q_pct:.0f}%)", expanded=True):
            # Score bar
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">
              <div style="flex:1;background:#e8eaf6;border-radius:8px;height:12px;overflow:hidden;">
                <div style="background:{bar_color};height:100%;width:{q_pct}%;border-radius:8px;"></div>
              </div>
              <div style="font-family:'Syne',sans-serif;font-weight:700;color:{bar_color};min-width:80px">
                {q_score}/{q_max} ({q_pct:.0f}%){'  ⚙️' if overridden else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Student answer
            st.markdown("**Your Answer:**")
            st.markdown(f'<div style="background:#f5f5f5;border-radius:8px;padding:0.8rem;color:#37474F">{res.get("student_answer","(no answer)") or "(no answer)"}</div>', unsafe_allow_html=True)

            # Feedback
            st.markdown("**Feedback:**")
            st.info(res.get("feedback", ""))

            # NLP breakdown
            sim = res.get("semantic_similarity", 0)
            kw = res.get("keyword_score", 0)
            coh = res.get("coherence_score", 0)

            c1, c2, c3 = st.columns(3)
            with c1:
                color = "#43A047" if sim >= 0.55 else ("#FFA726" if sim >= 0.35 else "#ef5350")
                st.markdown(f"""
                <div style="text-align:center;background:#f8f9ff;border-radius:10px;padding:0.8rem;">
                  <div style="font-size:1.4rem;font-weight:700;color:{color}">{sim:.0%}</div>
                  <div style="font-size:0.8rem;color:#546E7A">Semantic Match</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                color = "#43A047" if kw >= 0.7 else ("#FFA726" if kw >= 0.4 else "#ef5350")
                matched = res.get("matched_keywords", [])
                missed  = res.get("missed_keywords", [])
                st.markdown(f"""
                <div style="text-align:center;background:#f8f9ff;border-radius:10px;padding:0.8rem;">
                  <div style="font-size:1.4rem;font-weight:700;color:{color}">{kw:.0%}</div>
                  <div style="font-size:0.8rem;color:#546E7A">Keywords ({len(matched)} of {len(matched)+len(missed)})</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                color = "#43A047" if coh == 1.0 else ("#FFA726" if coh == 0.5 else "#ef5350")
                label = "Full" if coh == 1.0 else ("Partial" if coh == 0.5 else "Too Brief")
                st.markdown(f"""
                <div style="text-align:center;background:#f8f9ff;border-radius:10px;padding:0.8rem;">
                  <div style="font-size:1.4rem;font-weight:700;color:{color}">{label}</div>
                  <div style="font-size:0.8rem;color:#546E7A">Coherence</div>
                </div>
                """, unsafe_allow_html=True)

            # Show keywords
            if matched or missed:
                st.markdown("")
                if matched:
                    kw_html = " ".join(f'<span style="background:#e8f5e9;color:#2e7d32;border-radius:6px;padding:2px 8px;font-size:0.82rem;margin:2px">✓ {k}</span>' for k in matched)
                    st.markdown(f"<div>{kw_html}</div>", unsafe_allow_html=True)
                if missed:
                    kw_html = " ".join(f'<span style="background:#ffebee;color:#c62828;border-radius:6px;padding:2px 8px;font-size:0.82rem;margin:2px">✗ {k}</span>' for k in missed)
                    st.markdown(f"<div>{kw_html}</div>", unsafe_allow_html=True)
