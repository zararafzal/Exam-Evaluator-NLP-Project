# 🎓 Exam Evaluator AI

An automated exam grading system powered by NLP — built as a Bachelor's semester project.

## 🚀 Live Demo

Deploy instantly on [Streamlit Cloud](https://streamlit.io/cloud) — **free, no credit card required.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 👩‍🏫 **Teacher Portal** | Create exams, define model answers & keywords, view all submissions |
| 🧑‍🎓 **Student Portal** | Join via exam code, submit answers, get instant feedback |
| 🧠 **NLP Grading** | TF-IDF cosine similarity + keyword matching + coherence scoring |
| 📊 **Analytics Dashboard** | Score distributions, class averages, per-question breakdown |
| ✏️ **Score Override** | Teachers can manually adjust AI-assigned scores |
| ⏱️ **Timed Exams** | Configurable countdown timer per exam |

---

## 🧠 How the AI Grading Works

Each student answer is graded using a weighted formula:

```
Final Score = MaxMarks × [Semantic(0.50) + Keyword(0.30) + Coherence(0.20)]
```

| Signal | Weight | Method |
|---|---|---|
| Semantic Similarity | 50% | TF-IDF cosine similarity against model answer |
| Keyword Matching | 30% | Stemmed keyword presence check |
| Coherence | 20% | Answer length vs minimum word threshold |

---

## 🛠️ Tech Stack

- **Frontend/Backend**: Streamlit (Python)
- **NLP Engine**: Custom TF-IDF + cosine similarity (pure Python + numpy)
- **Storage**: JSON files (local) / session state (Streamlit Cloud)
- **Auth**: SHA-256 password hashing

---

## 📦 Deploy to Streamlit Cloud

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Exam Evaluator AI"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/exam-evaluator.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo → branch: `main` → main file: `app.py`
5. Click **Deploy** — done! ✅

---

## 💻 Run Locally

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/exam-evaluator.git
cd exam-evaluator

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

Open http://localhost:8501

---

## 📁 Project Structure

```
exam-evaluator/
├── app.py              # Main entry point & routing
├── grader.py           # NLP grading engine
├── database.py         # JSON-based persistence layer
├── teacher_views.py    # Teacher UI (dashboard, create exam, results)
├── student_views.py    # Student UI (take exam, view results)
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── config.toml     # Theme & server config
├── data/               # Auto-created: stores users, exams, submissions
└── README.md
```

---

## 🎯 Usage Guide

### For Teachers
1. Register as a **Teacher**
2. Click **"Create New Exam"**
3. Fill in: title, subject, duration
4. Per question: write question text, model answer, marks, and optional keywords
5. Publish → share the **6-character exam code** with students
6. View results anytime from your dashboard

### For Students
1. Register as a **Student**
2. Enter the **exam code** given by your teacher
3. Answer all questions within the time limit
4. Submit → instantly see your score, grade, and per-question feedback

---

## 📊 Grading Score Table

| Cosine Similarity | Grade Contribution |
|---|---|
| 0.85 – 1.00 | Excellent |
| 0.70 – 0.84 | Good |
| 0.55 – 0.69 | Partial |
| 0.40 – 0.54 | Weak |
| 0.00 – 0.39 | Off-topic |

---

## 📝 CV Description

> **Exam Evaluator** — AI product using NLP to automate exam grading; defined end-to-end product flows, implemented TF-IDF semantic similarity evaluation logic, keyword matching pipeline, and usability requirements; deployed as a full-stack Streamlit web application with teacher and student portals.

---

## 👤 Author

Built as a Bachelor's Semester Project  
[Your Name] | [Your University] | [Year]
