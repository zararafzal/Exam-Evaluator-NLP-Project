"""
Exam Evaluator — Main Entry Point
Run: streamlit run app.py
"""

import streamlit as st
import time
from database import authenticate, create_user, get_exams

st.set_page_config(
    page_title="ExamEval AI",
    page_icon="🎓",
    layout="centered",          # centred layout — no stretching
    initial_sidebar_state="collapsed",
)

# ── Global CSS: light + dark mode aware ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, p, div {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }
.block-container {
    padding: 2rem 1rem 3rem 1rem !important;
    max-width: 860px !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.18s ease !important;
    font-size: 0.95rem !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.18) !important;
}

/* Primary button colour fix */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    color: white !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* ── Metric ── */
[data-testid="metric-container"] {
    border-radius: 12px !important;
    border: 1px solid rgba(128,128,128,0.2) !important;
    padding: 0.8rem 1rem !important;
}

/* ── Custom component classes ── */
.nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0 1rem 0;
    border-bottom: 1px solid rgba(128,128,128,0.2);
    margin-bottom: 1.5rem;
}
.brand {
    font-size: 1.3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4F46E5, #7C3AED);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.page-title {
    font-size: 1.6rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}
.page-sub {
    font-size: 0.95rem;
    opacity: 0.6;
    margin-bottom: 1.5rem;
}
.card {
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.2);
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.9rem;
    background: transparent;
}
.code-pill {
    display: inline-block;
    font-family: 'Courier New', monospace;
    font-weight: 800;
    font-size: 1rem;
    letter-spacing: 4px;
    padding: 0.3rem 1rem;
    border-radius: 8px;
    background: rgba(79,70,229,0.12);
    color: #4F46E5;
    border: 1.5px solid rgba(79,70,229,0.3);
}
.badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.82rem;
}
.badge-green  { background: rgba(34,197,94,0.15);  color: #16a34a; }
.badge-yellow { background: rgba(234,179,8,0.15);  color: #b45309; }
.badge-red    { background: rgba(239,68,68,0.15);  color: #dc2626; }
.badge-blue   { background: rgba(79,70,229,0.12);  color: #4F46E5; }

.step-num {
    width: 30px; height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.85rem;
    color: white;
    flex-shrink: 0;
}
.divider { border: none; border-top: 1px solid rgba(128,128,128,0.2); margin: 1.2rem 0; }

/* Timer display */
.timer-box {
    text-align: center;
    padding: 0.8rem;
    border-radius: 12px;
    border: 2px solid;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("user", None), ("page", "home")]:
    if k not in st.session_state:
        st.session_state[k] = v

def nav(page: str):
    st.session_state.page = page
    st.rerun()

def require_auth(role=None):
    if not st.session_state.user:
        nav("home")
    if role and st.session_state.user.get("role") != role:
        st.error("Access denied.")
        st.stop()

# ── NAV BAR ───────────────────────────────────────────────────────────────────
def render_navbar():
    user = st.session_state.user
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown('<div class="brand">🎓 ExamEval AI</div>', unsafe_allow_html=True)
    with c2:
        if user:
            icon = "👩‍🏫" if user["role"] == "teacher" else "🧑‍🎓"
            rc1, rc2 = st.columns([2, 1])
            with rc1:
                st.markdown(f"<div style='text-align:right;font-weight:600;padding-top:6px'>{icon} {user['name']}</div>", unsafe_allow_html=True)
            with rc2:
                if st.button("Logout", key="logout_btn"):
                    st.session_state.user = None
                    st.session_state.page = "home"
                    st.rerun()
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
def page_home():
    # Brand header
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
      <div style="font-size:2.6rem; font-weight:800; background:linear-gradient(135deg,#4F46E5,#7C3AED);
                  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; line-height:1.2">
        🎓 ExamEval AI
      </div>
      <div style="opacity:0.6; margin-top:0.4rem; font-size:1rem">
        Automated exam grading powered by NLP — instant, fair, explainable.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Account CTA — very prominent ─────────────────────────────────────────
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(124,58,237,0.1));
                border: 1.5px solid rgba(79,70,229,0.25); border-radius: 16px;
                padding: 1.4rem 1.6rem; margin: 1rem 0 1.5rem 0; text-align:center;">
      <div style="font-size:1.15rem; font-weight:700; margin-bottom:0.3rem">
        👋 First time here? Create a free account to get started.
      </div>
      <div style="opacity:0.65; font-size:0.9rem">
        Teachers can create & grade exams. Students can take exams and see results instantly.
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("#### 👩‍🏫 I'm a Teacher")
        st.markdown("<div style='opacity:0.6;font-size:0.9rem;margin-bottom:0.6rem'>Create exams, define answers & keywords, view all results</div>", unsafe_allow_html=True)
        if st.button("Login or Register as Teacher →", use_container_width=True):
            nav("login_teacher")
    with c2:
        st.markdown("#### 🧑‍🎓 I'm a Student")
        st.markdown("<div style='opacity:0.6;font-size:0.9rem;margin-bottom:0.6rem'>Enter an exam code, submit answers, get instant AI feedback</div>", unsafe_allow_html=True)
        if st.button("Login or Register as Student →", use_container_width=True):
            nav("login_student")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Live Exam Codes ───────────────────────────────────────────────────────
    all_exams = list(get_exams().values())
    published = [e for e in all_exams if e.get("published", True)]

    st.markdown("#### 📋 Available Exams")
    if not published:
        st.markdown("<div style='opacity:0.5;font-size:0.9rem'>No exams published yet. Teachers can create one after logging in.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='opacity:0.6;font-size:0.88rem;margin-bottom:0.8rem'>Use one of these codes when joining an exam as a student.</div>", unsafe_allow_html=True)
        for exam in sorted(published, key=lambda e: e["created_at"], reverse=True):
            total_marks = sum(q["max_marks"] for q in exam["questions"])
            st.markdown(f"""
            <div class="card" style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;">
              <div>
                <div style="font-weight:700; font-size:1rem">{exam['title']}</div>
                <div style="opacity:0.6; font-size:0.85rem">{exam['subject']} &nbsp;·&nbsp; {len(exam['questions'])} questions &nbsp;·&nbsp; {total_marks} marks &nbsp;·&nbsp; {exam['duration_minutes']} min</div>
              </div>
              <div style="display:flex; align-items:center; gap:0.6rem;">
                <div class="code-pill">{exam['id']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # How it works
    st.markdown("#### ⚡ How it works")
    steps = [
        ("#4F46E5", "1", "Teacher creates exam", "Sets questions, model answers & optional keywords"),
        ("#7C3AED", "2", "Share the exam code", "Students see codes above or get them from their teacher"),
        ("#0EA5E9", "3", "Students submit answers", "Type answers in the exam — timer counts down live"),
        ("#10B981", "4", "AI grades instantly", "NLP engine scores semantic match, keywords & coherence"),
    ]
    for color, num, title, desc in steps:
        st.markdown(f"""
        <div style="display:flex; gap:0.9rem; align-items:flex-start; margin-bottom:0.7rem;">
          <div class="step-num" style="background:{color}">{num}</div>
          <div><div style="font-weight:700">{title}</div><div style="opacity:0.6;font-size:0.88rem">{desc}</div></div>
        </div>
        """, unsafe_allow_html=True)

# ── LOGIN / REGISTER ──────────────────────────────────────────────────────────
def page_login(role: str):
    render_navbar()
    icon  = "👩‍🏫" if role == "teacher" else "🧑‍🎓"
    label = role.capitalize()

    st.markdown(f'<div class="page-title">{icon} {label} Portal</div>', unsafe_allow_html=True)

    # Prominent "no account" prompt
    st.info("🆕 **New here?** Click the **Register** tab below to create a free account — it takes 30 seconds.", icon=None)

    tab_login, tab_reg = st.tabs(["🔑  Login", "✨  Register (New User)"])

    with tab_login:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            email    = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login →", use_container_width=True):
                user = authenticate(email.strip(), password)
                if user and user["role"] == role:
                    st.session_state.user = user
                    nav("teacher_dashboard" if role == "teacher" else "student_dashboard")
                elif user:
                    st.error(f"This account is a {user['role']} account. Please use the correct portal.")
                else:
                    st.error("Incorrect email or password. Please try again.")

    with tab_reg:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:600;margin-bottom:0.5rem'>Create a free {label} account</div>", unsafe_allow_html=True)
        with st.form("register_form"):
            name      = st.text_input("Full Name")
            email     = st.text_input("Email address", key="reg_email")
            password  = st.text_input("Password", type="password", key="reg_pw")
            password2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Create Account →", use_container_width=True):
                if not name or not email or not password:
                    st.error("Please fill in all fields.")
                elif password != password2:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    user = create_user(name.strip(), email.strip(), password, role)
                    if user:
                        st.session_state.user = user
                        st.success(f"✅ Welcome, {name}! Redirecting…")
                        time.sleep(0.7)
                        nav("teacher_dashboard" if role == "teacher" else "student_dashboard")
                    else:
                        st.error("That email is already registered. Please log in instead.")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    if st.button("← Back to Home"):
        nav("home")

# ── ROUTING ───────────────────────────────────────────────────────────────────
from teacher_views import page_teacher_dashboard, page_create_exam, page_exam_results
from student_views  import page_student_dashboard, page_take_exam, page_my_results

page = st.session_state.page

if page == "home":
    page_home()
elif page == "login_teacher":
    page_login("teacher")
elif page == "login_student":
    page_login("student")
elif page == "teacher_dashboard":
    require_auth("teacher"); render_navbar(); page_teacher_dashboard()
elif page == "create_exam":
    require_auth("teacher"); render_navbar(); page_create_exam()
elif page == "exam_results":
    require_auth("teacher"); render_navbar(); page_exam_results()
elif page == "student_dashboard":
    require_auth("student"); render_navbar(); page_student_dashboard()
elif page == "take_exam":
    require_auth("student"); render_navbar(); page_take_exam()
elif page == "my_results":
    require_auth("student"); render_navbar(); page_my_results()
else:
    nav("home")
