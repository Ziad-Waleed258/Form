import streamlit as st
from pypdf import PdfReader
import re
import random
import time

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="PDF MCQ Exam", layout="centered")

st.title("📘 PDF MCQ Exam System")
st.caption("Permanent wrong-question bank • Mastery learning")

# -------------------------------------------------
# Extract MCQs
# -------------------------------------------------
def extract_mcqs(text):
    questions = []
    blocks = re.split(r"\nQ\d+\.", text)

    for block in blocks[1:]:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        question = lines[0]
        options = {}
        correct_answer = None

        for line in lines:
            if re.match(r"[A-D]\.", line):
                letter = line[0]
                if "✔" in line:
                    correct_answer = letter
                options[letter] = line[2:].replace("✔", "").strip()

        if len(options) == 4 and correct_answer:
            questions.append({
                "question": question,
                "options": options,
                "answer": correct_answer,
                "explanation": "Review the related lecture notes or slides."
            })

    return questions

# -------------------------------------------------
# Upload PDF
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload MCQ PDF (✔ detected internally, hidden from user)",
    type="pdf"
)

# -------------------------------------------------
# Initialize state
# -------------------------------------------------
if uploaded_file and "questions" not in st.session_state:
    text = ""

    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    st.session_state.questions = extract_mcqs(text)
    random.shuffle(st.session_state.questions)

    st.session_state.score = 0
    st.session_state.start_time = time.time()

    st.session_state.correct_full = set()  
    st.session_state.wrong_ids = set()      

# -------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------
if "questions" in st.session_state:

    mode = st.sidebar.radio(
        "Mode",
        ["📝 Full Exam", "🔁 Only Wrong Questions"]
    )

    st.sidebar.metric("⏱ Time", int(time.time() - st.session_state.start_time))
    st.sidebar.metric("⭐ Score", st.session_state.score)
    st.sidebar.metric("❌ Wrong Bank Size", len(st.session_state.wrong_ids))

    st.divider()

    if mode == "📝 Full Exam":
        active_questions = st.session_state.questions
    else:
        active_questions = [
            q for q in st.session_state.questions
            if id(q) in st.session_state.wrong_ids
        ]

        if not active_questions:
            st.success("🎉 No questions in Wrong Bank yet!")
            st.stop()

    for q in active_questions:
        q_id = id(q)
        st.subheader(q["question"])

        selected = st.radio(
            "Choose one:",
            list(q["options"].keys()),
            format_func=lambda x: f"{x}. {q['options'][x]}",
            key=f"{mode}_{q_id}",
            disabled=(mode == "📝 Full Exam" and q_id in st.session_state.correct_full)
        )

        if st.button("Submit", key=f"submit_{mode}_{q_id}"):

            if selected == q["answer"]:
                st.success("✅ Correct")

                if mode == "📝 Full Exam":
                    if q_id not in st.session_state.correct_full:
                        st.session_state.score += 1
                    st.session_state.correct_full.add(q_id)

                st.info(f"📘 Explanation: {q['explanation']}")

            else:
                st.error("❌ Wrong — try again")

                if mode == "📝 Full Exam":
                    st.session_state.wrong_ids.add(q_id)

        st.divider()

    if st.button("🔀 Shuffle & Restart Exam"):
        random.shuffle(st.session_state.questions)
        st.session_state.score = 0
        st.session_state.start_time = time.time()
        st.session_state.correct_full = set()
        st.session_state.wrong_ids = set()
        st.rerun()

else:
    st.info("⬆ Upload your MCQ PDF to start the exam")
