"""
Exam Evaluator — Main Entry Point
Run: streamlit run app.py
"""

import streamlit as st
import time
from database import authenticate, create_user

st.set_page_config(
    page_title="ExamEval AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* Buttons */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 0.55rem 1.4rem;
    transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,0,0,0.15); }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    border-radius: 8px 8px 0 0;
}

/* Metric */
[data-testid="metric-container"] {
    background: #f8f9ff;
    border: 1px solid #e8eaf6;
    border-radius: 12px;
    padding: 1rem;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}

/* Success / error / info */
.stAlert { border-radius: 10px; }

/* Cards */
.eval-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    border: 1px solid #e8eaf6;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.score-badge {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}
.badge-green  { background:#e8f5e9; color:#2e7d32; }
.badge-yellow { background:#fff8e1; color:#f57f17; }
.badge-red    { background:#ffebee; color:#c62828; }

.brand-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3949AB, #1E88E5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.brand-sub {
    color: #546E7A;
    font-size: 1.05rem;
    font-weight: 300;
    margin-top: 0.4rem;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.4rem;
    color: #1a237e;
    margin-bottom: 0.2rem;
}

.exam-code-box {
    background: linear-gradient(135deg, #e8eaf6, #e3f2fd);
    border: 2px dashed #5c6bc0;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #3949AB;
    letter-spacing: 6px;
}

.progress-bar-wrap {
    background: #e8eaf6;
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
    margin: 0.3rem 0;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

hr.fancy { border: none; border-top: 2px solid #e8eaf6; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "home"


def nav(page: str):
    st.session_state.page = page
    st.rerun()


# ── Auth guard ────────────────────────────────────────────────────────────────
def require_auth(role=None):
    if not st.session_state.user:
        nav("home")
    if role and st.session_state.user.get("role") != role:
        st.error("Access denied.")
        st.stop()


# ── TOP NAV BAR ───────────────────────────────────────────────────────────────
def render_navbar():
    user = st.session_state.user
    c1, c2, c3 = st.columns([3, 6, 3])
    with c1:
        st.markdown('<span class="brand-title" style="font-size:1.5rem">🎓 ExamEval</span>', unsafe_allow_html=True)
    with c3:
        if user:
            role_icon = "👩‍🏫" if user["role"] == "teacher" else "🧑‍🎓"
            st.markdown(f"**{role_icon} {user['name']}**")
            if st.button("Logout", key="logout_btn"):
                st.session_state.user = None
                st.session_state.page = "home"
                st.rerun()
    st.markdown('<hr class="fancy">', unsafe_allow_html=True)


# ── LANDING PAGE ──────────────────────────────────────────────────────────────
def page_home():
    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("""
        <div style="padding: 3rem 0 2rem 0;">
          <div class="brand-title">AI-Powered<br>Exam Evaluator</div>
          <div class="brand-sub">Automated grading using NLP — instant feedback,<br>consistent scores, zero manual effort.</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 I'm a Teacher", use_container_width=True):
                nav("login_teacher")
        with c2:
            if st.button("🎓 I'm a Student", use_container_width=True):
                nav("login_student")

        st.markdown("""
        <div style="margin-top:2rem; display:flex; gap:2rem;">
          <div><span style="font-size:1.8rem">⚡</span><br><b>Instant</b><br><span style="color:#78909c;font-size:.9rem">Results in seconds</span></div>
          <div><span style="font-size:1.8rem">🧠</span><br><b>NLP-Powered</b><br><span style="color:#78909c;font-size:.9rem">Semantic understanding</span></div>
          <div><span style="font-size:1.8rem">📊</span><br><b>Analytics</b><br><span style="color:#78909c;font-size:.9rem">Full class insights</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#e8eaf6,#e3f2fd);border-radius:20px;padding:2rem;margin-top:2rem;">
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1.1rem;color:#3949AB;margin-bottom:1rem;">How it works</div>
          <div style="display:flex;flex-direction:column;gap:1rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
              <div style="background:#3949AB;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">1</div>
              <div><b>Teacher creates exam</b> with model answers &amp; keywords</div>
            </div>
            <div style="display:flex;align-items:center;gap:1rem;">
              <div style="background:#1E88E5;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">2</div>
              <div><b>Students submit</b> answers using a shared exam code</div>
            </div>
            <div style="display:flex;align-items:center;gap:1rem;">
              <div style="background:#00ACC1;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">3</div>
              <div><b>AI grades instantly</b> using semantic similarity + keywords</div>
            </div>
            <div style="display:flex;align-items:center;gap:1rem;">
              <div style="background:#43A047;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">4</div>
              <div><b>Detailed feedback</b> shown to both teacher and student</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── LOGIN / REGISTER ──────────────────────────────────────────────────────────
def page_login(role: str):
    render_navbar()
    icon = "👩‍🏫" if role == "teacher" else "🧑‍🎓"
    label = role.capitalize()
    st.markdown(f'<div class="section-title">{icon} {label} Portal</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login →", use_container_width=True)
            if submitted:
                user = authenticate(email.strip(), password)
                if user and user["role"] == role:
                    st.session_state.user = user
                    nav("teacher_dashboard" if role == "teacher" else "student_dashboard")
                elif user:
                    st.error(f"This account is registered as a {user['role']}, not {role}.")
                else:
                    st.error("Invalid email or password.")

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_pw")
            password2 = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account →", use_container_width=True)
            if submitted:
                if not name or not email or not password:
                    st.error("Please fill all fields.")
                elif password != password2:
                    st.error("Passwords do not match.")
                else:
                    user = create_user(name.strip(), email.strip(), password, role)
                    if user:
                        st.session_state.user = user
                        st.success("Account created!")
                        time.sleep(0.8)
                        nav("teacher_dashboard" if role == "teacher" else "student_dashboard")
                    else:
                        st.error("Email already registered.")

    st.markdown('<hr class="fancy">', unsafe_allow_html=True)
    if st.button("← Back to Home"):
        nav("home")


# ── ROUTING ───────────────────────────────────────────────────────────────────
from teacher_views import page_teacher_dashboard, page_create_exam, page_exam_results
from student_views import page_student_dashboard, page_take_exam, page_my_results

page = st.session_state.page

if page == "home":
    page_home()
elif page == "login_teacher":
    page_login("teacher")
elif page == "login_student":
    page_login("student")
elif page == "teacher_dashboard":
    require_auth("teacher")
    render_navbar()
    page_teacher_dashboard()
elif page == "create_exam":
    require_auth("teacher")
    render_navbar()
    page_create_exam()
elif page == "exam_results":
    require_auth("teacher")
    render_navbar()
    page_exam_results()
elif page == "student_dashboard":
    require_auth("student")
    render_navbar()
    page_student_dashboard()
elif page == "take_exam":
    require_auth("student")
    render_navbar()
    page_take_exam()
elif page == "my_results":
    require_auth("student")
    render_navbar()
    page_my_results()
else:
    nav("home")
