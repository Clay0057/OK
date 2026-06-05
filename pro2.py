import streamlit as st
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI

# ============================================================
# PATHS / PROFILE STORAGE
# ============================================================

BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "user_profile.json"


def load_profile() -> Dict[str, Any]:
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_profile(profile: Dict[str, Any]) -> None:
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ============================================================
# STREAMLIT LAYOUT
# ============================================================

st.set_page_config(page_title="Career Agent", layout="wide")

st.title("Career Agent with Optional GPT‑4o AI Coach")

# ============================================================
# SIDEBAR: API KEY + PROFILE
# ============================================================

st.sidebar.header("🔑 AI Coach Settings")

user_api_key = st.sidebar.text_input(
    "Enter your OpenAI API key (optional)",
    type="password",
    help="Leave empty to disable AI Coach"
)

ai_enabled = False
client = None

if user_api_key:
    try:
        client = OpenAI(api_key=user_api_key)
        ai_enabled = True
        st.sidebar.success("AI Coach enabled.")
    except Exception as e:
        st.sidebar.error(f"Invalid API key: {e}")
        ai_enabled = False
else:
    st.sidebar.info("AI Coach disabled. Enter a key to enable GPT‑4o.")

st.sidebar.markdown("---")
st.sidebar.header("👤 User Profile")

profile = load_profile()
default_name = profile.get("name", "")
default_title = profile.get("title", "")
default_location = profile.get("location", "")

name = st.sidebar.text_input("Name", value=default_name)
title = st.sidebar.text_input("Target Role / Title", value=default_title)
location = st.sidebar.text_input("Location", value=default_location)

if st.sidebar.button("Save Profile"):
    profile.update({"name": name, "title": title, "location": location})
    save_profile(profile)
    st.sidebar.success("Profile saved to user_profile.json")


# ============================================================
# MAIN LAYOUT: JOB + RESUME
# ============================================================

col_job, col_resume = st.columns(2)

with col_job:
    st.subheader("📄 Job Description")
    job_source = st.radio(
        "Job input method",
        ["Paste text", "From URL"],
        horizontal=True
    )

    job_description = ""

    if job_source == "Paste text":
        job_description = st.text_area(
            "Paste job description",
            height=250,
            placeholder="Paste the full job description here..."
        )
    else:
        job_url = st.text_input("Job URL")
        if st.button("Fetch job from URL"):
            st.warning("URL import not implemented yet.")
        job_description = st.text_area(
            "Job description (editable)",
            height=250,
            placeholder="If you fetched from URL, paste or edit here..."
        )

with col_resume:
    st.subheader("📑 Resume")
    resume_source = st.radio(
        "Resume input method",
        ["Paste text", "Upload file"],
        horizontal=True
    )

    resume_text = ""

    if resume_source == "Paste text":
        resume_text = st.text_area(
            "Paste resume",
            height=250,
            placeholder="Paste your resume here..."
        )
    else:
        uploaded_file = st.file_uploader("Upload resume (TXT or PDF)", type=["txt", "pdf"])
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain":
                resume_text = uploaded_file.read().decode("utf-8", errors="ignore")
            else:
                st.warning("PDF parsing not implemented. Convert to text first.")
        resume_text = st.text_area(
            "Resume (editable)",
            value=resume_text,
            height=250
        )


# ============================================================
# MATCHING ENGINE
# ============================================================

st.markdown("---")
st.subheader("🎯 Job–Resume Match Summary")

def simple_match_score(job: str, resume: str) -> Dict[str, Any]:
    if not job or not resume:
        return {"score": 0, "missing_keywords": [], "present_keywords": []}

    job_words = set(w.lower() for w in job.split() if len(w) > 4)
    resume_words = set(w.lower() for w in resume.split() if len(w) > 4)

    present = sorted(list(job_words & resume_words))
    missing = sorted(list(job_words - resume_words))

    score = int(100 * len(present) / max(len(job_words), 1))

    return {
        "score": score,
        "missing_keywords": missing[:30],
        "present_keywords": present[:30],
    }


if st.button("Analyze Match"):
    if not job_description or not resume_text:
        st.error("Please provide both job description and resume.")
    else:
        result = simple_match_score(job_description, resume_text)
        st.write(f"**Match score:** {result['score']} / 100")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Present keywords in resume:**")
            if result["present_keywords"]:
                st.write(", ".join(result["present_keywords"]))
            else:
                st.write("None detected.")

        with col2:
            st.markdown("**Missing keywords from resume:**")
            if result["missing_keywords"]:
                st.write(", ".join(result["missing_keywords"]))
            else:
                st.write("None detected.")


# ============================================================
# RESUME + COVER LETTER GENERATION
# ============================================================

st.markdown("---")
st.subheader("🛠 AI Resume & Cover Letter (GPT‑4o)")

col_r1, col_r2 = st.columns(2)

with col_r1:
    if st.button("Generate optimized resume (GPT‑4o)"):
        if not ai_enabled:
            st.error("AI Coach is disabled. Enter an API key in the sidebar.")
        elif not job_description or not resume_text:
            st.error("Provide both job description and resume.")
        else:
            with st.spinner("Generating optimized resume..."):
                prompt = (
                    "Rewrite the following resume to better match the job description, "
                    "while keeping it truthful and concise.\n\n"
                    f"Job description:\n{job_description}\n\n"
                    f"Current resume:\n{resume_text}\n\n"
                    "Return only the improved resume text."
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a precise, practical career assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )
                improved_resume = resp.choices[0].message.content
                st.text_area("Optimized resume", improved_resume, height=300)

with col_r2:
    if st.button("Generate cover letter (GPT‑4o)"):
        if not ai_enabled:
            st.error("AI Coach is disabled. Enter an API key in the sidebar.")
        elif not job_description or not resume_text:
            st.error("Provide both job description and resume.")
        else:
            with st.spinner("Generating cover letter..."):
                prompt = (
                    "Write a tailored cover letter for the following job, based on the resume.\n\n"
                    f"Job description:\n{job_description}\n\n"
                    f"Resume:\n{resume_text}\n\n"
                    "Return only the cover letter text."
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a precise, practical career assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )
                cover_letter = resp.choices[0].message.content
                st.text_area("Cover letter", cover_letter, height=300)


# ============================================================
# AI COACH (OPTIONAL GPT‑4o)
# ============================================================

st.markdown("---")
st.subheader("🤖 AI Career Coach (GPT‑4o)")

if "coach_history" not in st.session_state:
    st.session_state.coach_history = []

if not ai_enabled:
    st.info("AI Coach is disabled. Enter an API key in the sidebar to enable it.")
else:
    # Show chat history
    for msg in st.session_state.coach_history:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Coach:** {msg['content']}")

    user_msg = st.text_input("Ask the AI Coach anything:")

    if st.button("Send to Coach"):
        if user_msg.strip():
            st.session_state.coach_history.append({"role": "user", "content": user_msg})

            messages: List[Dict[str, str]] = [
                {
                    "role": "system",
                    "content": (
                        "You are a direct, practical AI career coach. You give concise, honest advice "
                        "without fluff. You focus on job fit, resume impact, and realistic next steps."
                    ),
                }
            ]

            # Add context from profile
            context_parts = []
            if name:
                context_parts.append(f"User name: {name}")
            if title:
                context_parts.append(f"Target role: {title}")
            if location:
                context_parts.append(f"Location: {location}")
            if job_description:
                context_parts.append("Job description provided.")
            if resume_text:
                context_parts.append("Resume provided.")

            if context_parts:
                messages.append(
                    {"role": "system", "content": "Context: " + " | ".join(context_parts)}
                )

            # Add chat history
            for h in st.session_state.coach_history:
                messages.append({"role": h["role"], "content": h["content"]})

            with st.spinner("Coach is thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                coach_reply = resp.choices[0].message.content
                st.session_state.coach_history.append({"role": "assistant", "content": coach_reply})
                st.markdown(f"**Coach:** {coach_reply}")
