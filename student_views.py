"""Student Views — Dashboard, Take Exam (with live timer), My Results"""

import streamlit as st
import time
from database import (
    get_exam, get_exams, save_submission, get_student_submissions,
    has_student_submitted, get_submission
)
from grader import grade_answer

def nav(page):
    st.session_state.page = page
    st.rerun()

# ── STUDENT DASHBOARD ─────────────────────────────────────────────────────────
def page_student_dashboard():
    user = st.session_state.user
    st.markdown(f'<div class="page-title">🧑‍🎓 Student Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">Hello, {user["name"]}. Join an exam or review your past results.</div>', unsafe_allow_html=True)

    # ── Join exam ─────────────────────────────────────────────────────────────
    st.markdown("**Join an Exam**")
    with st.form("join_form"):
        c1, c2 = st.columns([3, 1])
        with c1:
            code = st.text_input("Enter Exam Code", placeholder="e.g. AB12CD", label_visibility="collapsed")
        with c2:
            go = st.form_submit_button("Join →", use_container_width=True)
        if go:
            code = code.strip().upper()
            if not code:
                st.error("Please enter an exam code.")
            else:
                exam = get_exam(code)
                if not exam:
                    st.error("Exam not found. Double-check the code.")
                elif has_student_submitted(code, user["id"]):
                    st.warning("You've already submitted this exam. See your result below.")
                else:
                    st.session_state.active_exam_id   = code
                    st.session_state.student_answers  = {}
                    st.session_state.exam_start_time  = time.time()
                    nav("take_exam")

    # ── Available exams ───────────────────────────────────────────────────────
    all_exams = [e for e in get_exams().values() if e.get("published", True)]
    if all_exams:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown("**Available Exams — use one of these codes above**")
        for exam in sorted(all_exams, key=lambda e: e["created_at"], reverse=True):
            already = has_student_submitted(exam["id"], user["id"])
            status  = '<span class="badge badge-green">✓ Submitted</span>' if already else '<span class="badge badge-blue">Open</span>'
            st.markdown(f"""
            <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
              <div>
                <div style="font-weight:700">{exam['title']}</div>
                <div style="opacity:0.6;font-size:0.85rem">{exam['subject']} &nbsp;·&nbsp; {len(exam['questions'])} questions &nbsp;·&nbsp; {exam['duration_minutes']} min</div>
              </div>
              <div style="display:flex;gap:0.6rem;align-items:center">
                {status}
                <span class="code-pill">{exam['id']}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Past submissions ──────────────────────────────────────────────────────
    subs = get_student_submissions(user["id"])
    if subs:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(f"**My Results ({len(subs)})**")
        for sub in sorted(subs, key=lambda s: s["submitted_at"], reverse=True):
            pct   = sub["percentage"]
            badge = "badge-green" if pct >= 65 else ("badge-yellow" if pct >= 40 else "badge-red")
            emoji = "🟢" if pct >= 65 else ("🟡" if pct >= 40 else "🔴")
            exam  = get_exam(sub["exam_id"])
            title = exam["title"] if exam else sub["exam_id"]
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div class="card">
                  <div style="font-weight:700">{emoji} {title}</div>
                  <div style="opacity:0.6;font-size:0.85rem">Code: {sub['exam_id']}</div>
                  <div style="margin-top:0.4rem"><span class="badge {badge}">{sub['total_score']}/{sub['total_marks']} — {pct}%</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
                if st.button("Details", key=f"det_{sub['id']}", use_container_width=True):
                    st.session_state.selected_submission_id = sub["id"]
                    nav("my_results")

# ── TAKE EXAM (with functional live timer) ────────────────────────────────────
def page_take_exam():
    user    = st.session_state.user
    exam_id = st.session_state.get("active_exam_id")
    if not exam_id:
        nav("student_dashboard"); return

    exam = get_exam(exam_id)
    if not exam:
        st.error("Exam not found."); nav("student_dashboard"); return

    # ── Timer ─────────────────────────────────────────────────────────────────
    start_time    = st.session_state.get("exam_start_time", time.time())
    duration_secs = exam["duration_minutes"] * 60
    elapsed       = time.time() - start_time
    remaining     = max(0.0, duration_secs - elapsed)
    timed_out     = remaining <= 0

    mins = int(remaining // 60)
    secs = int(remaining % 60)

    if remaining < 60:
        t_color = "#dc2626"
    elif remaining < 300:
        t_color = "#b45309"
    else:
        t_color  = "#16a34a"

    # ── Header ────────────────────────────────────────────────────────────────
    hc1, hc2, hc3 = st.columns([3, 1, 1])
    with hc1:
        st.markdown(f'<div class="page-title" style="margin-bottom:0">{exam["title"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="opacity:0.55;font-size:0.9rem">{exam["subject"]}</div>', unsafe_allow_html=True)
    with hc2:
        total_marks = sum(q["max_marks"] for q in exam["questions"])
        st.markdown(f"""
        <div style="text-align:center;padding:0.6rem;border-radius:10px;background:rgba(128,128,128,0.08);border:1px solid rgba(128,128,128,0.2)">
          <div style="font-size:1.3rem;font-weight:800">{len(exam['questions'])}</div>
          <div style="font-size:0.75rem;opacity:0.6">{total_marks} marks</div>
        </div>
        """, unsafe_allow_html=True)
    with hc3:
        st.markdown(f"""
        <div style="text-align:center;padding:0.6rem;border-radius:10px;
                    background:rgba(128,128,128,0.08);
                    border:2px solid {t_color};">
          <div style="font-size:1.3rem;font-weight:800;color:{t_color}">{mins:02d}:{secs:02d}</div>
          <div style="font-size:0.75rem;opacity:0.6">remaining</div>
        </div>
        """, unsafe_allow_html=True)

    if timed_out:
        st.error("⏰ Time's up! Your answers are being submitted…")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Questions ─────────────────────────────────────────────────────────────
    if "student_answers" not in st.session_state:
        st.session_state.student_answers = {}

    answers = {}
    for i, q in enumerate(exam["questions"]):
        st.markdown(f"""
        <div style="background:rgba(79,70,229,0.07);border-radius:12px;
                    padding:0.9rem 1.1rem;margin-bottom:0.4rem;
                    border-left:4px solid #4F46E5;">
          <div style="font-weight:700;font-size:0.95rem">
            Question {i+1}
            <span style="font-size:0.78rem;background:rgba(79,70,229,0.15);color:#4F46E5;
                         border-radius:6px;padding:1px 8px;margin-left:6px">{q['max_marks']} marks</span>
          </div>
          <div style="margin-top:0.35rem">{q['text']}</div>
        </div>
        """, unsafe_allow_html=True)

        ans = st.text_area(
            f"Answer {i+1}",
            value=st.session_state.student_answers.get(i, ""),
            key=f"ans_{i}",
            placeholder="Type your answer here…",
            height=110,
            disabled=timed_out,
            label_visibility="collapsed",
        )
        answers[i] = ans

        wc        = len(ans.split()) if ans.strip() else 0
        min_w     = q.get("min_words", 0)
        wc_color  = "#16a34a" if (min_w == 0 or wc >= min_w) else ("#b45309" if wc > 0 else "#6b7280")
        min_label = f"(min {min_w})" if min_w > 0 else ""
        st.markdown(f'<div style="font-size:0.78rem;color:{wc_color};text-align:right;margin-top:-0.3rem">{wc} words {min_label}</div>', unsafe_allow_html=True)
        st.markdown("")

    # Save answers to session state on every render
    if not timed_out:
        st.session_state.student_answers = answers

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        submit = st.button("🚀 Submit Exam", type="primary", use_container_width=True, disabled=timed_out and False)
    with c2:
        cancel = st.button("✕ Cancel", use_container_width=True)

    if cancel:
        nav("student_dashboard")

    should_submit = submit or timed_out

    if should_submit:
        final_answers = st.session_state.get("student_answers", answers)
        with st.spinner("🧠 Grading your answers with AI…"):
            results      = []
            total_score  = 0.0
            total_marks  = 0.0
            for i, q in enumerate(exam["questions"]):
                student_ans = (final_answers.get(i) or "").strip()
                result = grade_answer(
                    student_answer=student_ans if student_ans else "(no answer)",
                    model_answer=q["model_answer"],
                    keywords=q.get("keywords", []),
                    max_marks=q["max_marks"],
                    min_words=q.get("min_words", 0),
                )
                result["question_text"]  = q["text"]
                result["student_answer"] = student_ans
                results.append(result)
                total_score += result["score"]
                total_marks += q["max_marks"]

        sub = save_submission(
            exam_id=exam_id, student_id=user["id"], student_name=user["name"],
            results=results, total_score=total_score, total_marks=total_marks,
        )
        st.session_state.selected_submission_id = sub["id"]
        st.success("✅ Submitted! Loading your results…")
        time.sleep(0.8)
        nav("my_results")

    # ── Live timer refresh ────────────────────────────────────────────────────
    # Refresh every 30 seconds so the timer ticks visibly
    if not timed_out and remaining > 0:
        refresh_interval = 30  # seconds
        st.markdown(
            f'<meta http-equiv="refresh" content="{refresh_interval}">',
            unsafe_allow_html=True
        )

# ── MY RESULTS ─────────────────────────────────────────────────────────────────
def page_my_results():
    sub_id = st.session_state.get("selected_submission_id")
    if not sub_id:
        nav("student_dashboard"); return

    sub = get_submission(sub_id)
    if not sub:
        st.error("Result not found."); nav("student_dashboard"); return

    exam       = get_exam(sub["exam_id"])
    exam_title = exam["title"] if exam else sub["exam_id"]

    if st.button("← Back to Dashboard"):
        nav("student_dashboard")

    pct         = sub["percentage"]
    total_score = sub["total_score"]
    total_marks = sub["total_marks"]

    if pct >= 85:   grade, g_color = "A — Excellent",  "#16a34a"
    elif pct >= 70: grade, g_color = "B — Good",       "#1d4ed8"
    elif pct >= 55: grade, g_color = "C — Average",    "#b45309"
    elif pct >= 40: grade, g_color = "D — Pass",       "#b45309"
    else:           grade, g_color = "F — Fail",       "#dc2626"

    st.markdown(f'<div class="page-title">📋 {exam_title}</div>', unsafe_allow_html=True)

    # Score card
    bar_color = "#16a34a" if pct >= 55 else "#dc2626"
    st.markdown(f"""
    <div style="border-radius:16px;padding:1.8rem;text-align:center;margin:1rem 0;
                background:linear-gradient(135deg,#4F46E5,#7C3AED);color:white;">
      <div style="font-size:3rem;font-weight:800;line-height:1">{total_score}</div>
      <div style="opacity:0.75;font-size:1rem">out of {total_marks} marks</div>
      <div style="margin:1rem auto 0.3rem;max-width:260px;background:rgba(255,255,255,0.25);
                  border-radius:20px;height:10px;overflow:hidden;">
        <div style="background:white;height:100%;width:{pct}%;border-radius:20px;"></div>
      </div>
      <div style="font-size:1.5rem;font-weight:800;margin-top:0.4rem">{pct}%</div>
      <div style="font-weight:600;opacity:0.9">{grade}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("**Question-by-Question Breakdown**")

    for i, res in enumerate(sub["results"]):
        q_score    = res["score"]
        q_max      = res["max_marks"]
        q_pct      = (q_score / q_max * 100) if q_max else 0
        bar_color  = "#16a34a" if q_pct >= 65 else ("#b45309" if q_pct >= 40 else "#dc2626")
        overridden = res.get("overridden", False)

        with st.expander(f"Q{i+1}: {res.get('question_text','')[:55]}… — {q_score}/{q_max} ({q_pct:.0f}%)", expanded=True):
            # Progress bar
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.8rem">
              <div style="flex:1;background:rgba(128,128,128,0.15);border-radius:8px;height:10px;overflow:hidden;">
                <div style="background:{bar_color};height:100%;width:{q_pct}%;border-radius:8px;"></div>
              </div>
              <div style="font-weight:700;color:{bar_color};min-width:90px">
                {q_score}/{q_max} ({q_pct:.0f}%) {'⚙️' if overridden else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Your answer:**")
            answer_text = res.get("student_answer") or "(no answer)"
            st.markdown(f'<div style="background:rgba(128,128,128,0.08);border-radius:8px;padding:0.7rem;font-size:0.93rem">{answer_text}</div>', unsafe_allow_html=True)

            st.markdown("**Feedback:**")
            st.info(res.get("feedback", ""))

            # NLP breakdown
            sim = res.get("semantic_similarity", 0)
            kw  = res.get("keyword_score", 0)
            coh = res.get("coherence_score", 0)

            c1, c2, c3 = st.columns(3)
            def metric_card(col, label, value_str, color):
                col.markdown(f"""
                <div style="text-align:center;background:rgba(128,128,128,0.07);border-radius:10px;padding:0.7rem;">
                  <div style="font-size:1.3rem;font-weight:800;color:{color}">{value_str}</div>
                  <div style="font-size:0.75rem;opacity:0.6">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            metric_card(c1, "Semantic Match",  f"{sim:.0%}", "#16a34a" if sim>=0.55 else ("#b45309" if sim>=0.35 else "#dc2626"))
            metric_card(c2, "Keywords",        f"{kw:.0%}",  "#16a34a" if kw>=0.7  else ("#b45309" if kw>=0.4  else "#dc2626"))
            coh_label = "Full" if coh >= 1.0 else ("Partial" if coh >= 0.5 else "Brief")
            metric_card(c3, "Coherence",       coh_label,    "#16a34a" if coh>=1.0  else ("#b45309" if coh>=0.5  else "#dc2626"))

            matched = res.get("matched_keywords", [])
            missed  = res.get("missed_keywords",  [])
            if matched or missed:
                st.markdown("")
                if matched:
                    kw_html = " ".join(f'<span style="background:rgba(34,197,94,0.15);color:#16a34a;border-radius:6px;padding:2px 8px;font-size:0.82rem">✓ {k}</span>' for k in matched)
                    st.markdown(kw_html, unsafe_allow_html=True)
                if missed:
                    kw_html = " ".join(f'<span style="background:rgba(239,68,68,0.15);color:#dc2626;border-radius:6px;padding:2px 8px;font-size:0.82rem">✗ {k}</span>' for k in missed)
                    st.markdown(kw_html, unsafe_allow_html=True)
