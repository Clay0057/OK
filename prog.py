# Run this in PowerShell:
# setx OPENAI_API_KEY "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"




import streamlit as st
import re
import json
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# API KEY INPUT IN UI
st.sidebar.header("🔑 API Key")
user_api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")

if user_api_key:
    os.environ["OPENAI_API_KEY"] = user_api_key

if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
    st.error("Please enter your OpenAI API key in the sidebar to continue.")
    st.stop()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ============================================================
# PROFILE SAVE / LOAD (PERSISTENT MEMORY)
# ============================================================
PROFILE_FILE = "user_profile.json"

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return None


# ============================================================
# FETCH JOB FROM URL
# ============================================================
def fetch_job_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        candidates = [
            {"tag": "div", "class": "job-description"},
            {"tag": "div", "class": "description"},
            {"tag": "section", "class": "job"},
            {"tag": "div", "id": "jobDescriptionText"},
            {"tag": "div", "id": "job-details"},
            {"tag": "article"},
            {"tag": "main"},
            {"tag": "body"}
        ]

        for c in candidates:
            block = soup.find(c.get("tag"), class_=c.get("class"), id=c.get("id"))
            if block:
                return block.get_text(separator="\n")

        return soup.get_text(separator="\n")

    except Exception as e:
        return f"Error fetching job: {e}"


# ============================================================
# IT KEYWORDS (ROUGH MATCHING)
# ============================================================
IT_KEYWORDS = [
    "network", "computer", "systems", "information", "server",
    "communications", "wireless", "wired", "fibre", "fiber",
    "broadband", "technology", "technician", "support",
    "data", "infrastructure", "hardware", "software",
    "security", "it", "technical", "administrator",
    "ad", "active directory", "m365", "help desk",
    "peripherals"
]

def extract_skills(text):
    text = text.lower()
    found = []
    for word in IT_KEYWORDS:
        if word.lower() in text:
            found.append(word)
    return list(set(found))


# ============================================================
# UNIVERSAL SALARY EXTRACTION
# ============================================================
def extract_salary(text):
    text = text.lower()

    patterns = [
        r"\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?\s*-\s*\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?",
        r"\$\d{4,6}\s*-\s*\$\d{4,6}",
        r"\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?",
        r"\$\d{4,6}(?:\.\d{2})?",
        r"\$\d{2,3}k\s*-\s*\$\d{2,3}k",
        r"\$\d{2,3}k",
        r"\$\d{2,5}\s*(?:per month|monthly|per year|yearly|/month|/year)",
        r"\$\d{1,3}(?:,\d{3})+(?:\.\d{2})?\s*(?:per month|monthly|per year|yearly)"
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group()

    return "Not listed"


# ============================================================
# EMPLOYER + LOCATION EXTRACTION
# ============================================================
def extract_employer(text):
    if "canadian armed forces" in text.lower() or "caf" in text.lower():
        return "Canadian Armed Forces"
    return "Not specified"

def extract_location(text):
    if "halifax" in text.lower():
        return "Halifax, NS"
    if "canada" in text.lower():
        return "Canada (National)"
    if "remote" in text.lower():
        return "Remote"
    return "Not specified"


# ============================================================
# MATCH ENGINE
# ============================================================
def analyze_match(user_skills, job_text):
    job_text = job_text.lower()
    matched = []
    missing = []

    for skill in user_skills:
        if skill.lower() in job_text:
            matched.append(skill)
        else:
            missing.append(skill)

    score = int((len(matched) / len(user_skills)) * 100) if user_skills else 0
    return score, matched, missing


# ============================================================
# SCORE EXPLANATION
# ============================================================
def explain_score(score):
    if score >= 80:
        return "🟢 Excellent match — highly aligned."
    elif score >= 60:
        return "🟡 Strong match — many key requirements met."
    elif score >= 30:
        return "🟠 Moderate match — noticeable gaps."
    else:
        return "🔴 Weak match — low alignment."


# ============================================================
# FULL-LENGTH RESUME GENERATOR
# ============================================================
def optimize_resume(user_skills, matched_skills, missing_skills, job_title):
    summary = (
        f"As an IT professional with hands-on experience across systems administration, network operations, "
        f"and technical support, I bring a strong foundation in {', '.join(matched_skills)}. "
        f"My background includes supporting enterprise environments, resolving complex technical issues, "
        f"and maintaining reliable infrastructure. I am actively strengthening my capabilities in "
        f"{', '.join(missing_skills)} to fully align with the requirements of the {job_title} role."
        if missing_skills else
        f"As an IT professional with hands-on experience across systems administration, network operations, "
        f"and technical support, I bring a strong foundation in {', '.join(matched_skills)}. "
        f"My background includes supporting enterprise environments, resolving complex technical issues, "
        f"and maintaining reliable infrastructure. I am fully aligned with the requirements of the {job_title} role."
    )

    resume_text = f"""
==================================================
PROFESSIONAL SUMMARY
==================================================
{summary}

I have a proven track record of delivering stable, secure, and efficient IT operations. My experience spans
user support, system maintenance, hardware and software troubleshooting, and network connectivity. I excel in
fast-paced environments where reliability, communication, and problem-solving are essential.

==================================================
CORE TECHNICAL SKILLS
==================================================
Matched Skills:
- {', '.join(matched_skills) if matched_skills else 'None detected'}

Skills to Develop:
- {', '.join(missing_skills) if missing_skills else 'No major gaps'}

Your Skills:
- {', '.join(user_skills)}

==================================================
PROFESSIONAL EXPERIENCE
==================================================
IT Support / Systems & Network Operations
• Provided technical support for users, systems, and network environments  
• Maintained Active Directory, M365, and enterprise authentication systems  
• Diagnosed and resolved hardware, software, and connectivity issues  
• Supported servers, peripherals, and communication systems  
• Ensured secure, stable, and efficient IT operations  
• Documented procedures, incidents, and resolutions  

Technical Troubleshooting & Infrastructure Support
• Performed root-cause analysis for recurring issues  
• Supported wired and wireless network infrastructure  
• Maintained system uptime and monitored performance  
• Assisted with deployments, upgrades, and configuration changes  

==================================================
EDUCATION & CERTIFICATIONS
==================================================
• CompTIA A+  
• CCNA  
• Additional certifications as applicable  

==================================================
ADDITIONAL STRENGTHS
==================================================
• Strong communication and user support skills  
• Ability to learn new technologies quickly  
• Reliable, detail-oriented, and proactive  
• Comfortable in structured or dynamic environments  
"""
    return resume_text


# ============================================================
# FULL-LENGTH COVER LETTER GENERATOR
# ============================================================
def generate_cover_letter(job_title, company, matched_skills, missing_skills):
    skill_line = (
        f"{', '.join(matched_skills)}"
        if matched_skills else
        "core IT support, troubleshooting, and system administration"
    )

    growth_line = (
        f"In addition, I am actively developing skills in {', '.join(missing_skills)}, "
        f"which strengthens my long-term fit for this role."
        if missing_skills else
        ""
    )

    return f"""
Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}. With a strong background in IT systems,
network operations, and technical support, I bring hands-on experience that aligns closely with the needs of this role.
My work has consistently focused on maintaining reliable infrastructure, supporting users, and ensuring secure and
efficient technical operations.

Throughout my experience, I have developed solid capabilities in {skill_line}. I have supported enterprise environments,
resolved complex technical issues, and contributed to stable system performance. I take pride in delivering clear
communication, thorough troubleshooting, and dependable support in fast-paced environments.

{growth_line}

I am confident that my technical foundation, combined with my commitment to continuous learning, would allow me to make
a meaningful contribution to your team. I am highly motivated, adaptable, and dedicated to maintaining the reliability
and security of IT systems.

I would welcome the opportunity to discuss how my skills and experience align with the needs of your organization.
Thank you for your time and consideration.

Sincerely,  
Applicant
"""


# ============================================================
# OFFER PROBABILITY MODEL
# ============================================================
def offer_probability(match_score, job_text):
    job_text = job_text.lower()
    base = match_score

    if any(x in job_text for x in ["government", "university", "cmhc"]):
        base += 10

    if "senior" in job_text and match_score < 60:
        base -= 15

    if "help desk" in job_text:
        base -= 10

    base = max(0, min(100, base))

    if base >= 75:
        level = "🟢 High Offer Probability"
    elif base >= 50:
        level = "🟡 Medium"
    else:
        level = "🔴 Low"

    return base, level


# ============================================================
# CAREER GOAL COMPARISON
# ============================================================
def compare_to_goals(job_info, goals):
    advice = []

    if any(r in job_info["title"].lower() for r in goals["target_roles"]):
        advice.append("✔️ Role aligns with your target path.")
    else:
        advice.append("⚠️ Role does not match your target job titles.")

    if job_info["location"] != "Not specified":
        if any(loc in job_info["location"].lower() for loc in goals["preferred_locations"]):
            advice.append("✔️ Location fits your preferences.")
        else:
            advice.append(f"⚠️ Location ({job_info['location']}) is outside your preferred areas.")

    if job_info["salary"] != "Not listed":
        nums = re.findall(r"\d+", job_info["salary"])
        if nums:
            salary_num = int(nums[0]) * (1000 if "k" in job_info["salary"].lower() else 1)
            if salary_num >= goals["minimum_salary"]:
                advice.append("✔️ Salary meets your expectations.")
            else:
                advice.append("⚠️ Salary may be below your target range.")

    if any(e in job_info["employer"].lower() for e in goals["preferred_employers"]):
        advice.append("✔️ Employer matches preferred sectors.")
    else:
        advice.append("ℹ️ Employer is acceptable but not preferred.")

    missing_growth = [s for s in goals["growth_skills"] if s not in job_info["skills"]]
    if missing_growth:
        advice.append(f"📘 Consider improving: {', '.join(missing_growth)}")
    else:
        advice.append("✔️ You meet your growth skill targets.")

    return advice


# ============================================================
# AI JOB SUMMARY
# ============================================================
def generate_job_summary(job_text):
    job_text = job_text.strip()

    keywords = extract_skills(job_text)
    salary = extract_salary(job_text)
    location = extract_location(job_text)
    employer = extract_employer(job_text)

    summary = f"""
Summary of Job Posting:

• Employer: {employer}
• Location: {location}
• Salary: {salary}

Key Responsibilities:
- Work related to: {", ".join(keywords) if keywords else "general IT operations"}.
- Likely includes maintaining systems, supporting users, and working with IT infrastructure.

Ideal Candidate:
- Experience in: {", ".join(keywords) if keywords else "IT support or technical operations"}.
- Strong interest in technology, troubleshooting, and system reliability.

Overall:
This appears to be an IT-focused role around systems, networks, communications, and technical support.
"""
    return summary


# ============================================================
# AI COACH (DIRECT, STREAMING, MULTI-TURN)
# ============================================================
def build_coach_system_prompt(job_desc, job_info, user_skills, matched_skills, missing_skills,
                              match_score, offer_score, offer_level, career_goals,
                              optimized_resume, cover_letter):
    return {
        "role": "system",
        "content": f"""
You are a direct, tactical career coach. No fluff. Give blunt, practical advice.

You are helping a user evaluate an IT job opportunity and plan their career moves.

JOB DESCRIPTION:
{job_desc}

EXTRACTED JOB INFO:
- Title: {job_info.get('title', 'N/A')}
- Employer: {job_info.get('employer', 'N/A')}
- Location: {job_info.get('location', 'N/A')}
- Salary: {job_info.get('salary', 'N/A')}
- Skills in posting: {', '.join(job_info.get('skills', []))}

USER PROFILE:
- Skills: {', '.join(user_skills)}
- Matched skills: {', '.join(matched_skills)}
- Missing skills: {', '.join(missing_skills)}
- Match score: {match_score}%
- Offer probability: {offer_score}% ({offer_level})

CAREER GOALS:
- Target roles: {', '.join(career_goals['target_roles'])}
- Preferred locations: {', '.join(career_goals['preferred_locations'])}
- Minimum salary: {career_goals['minimum_salary']}
- Preferred employers: {', '.join(career_goals['preferred_employers'])}
- Growth skills: {', '.join(career_goals['growth_skills'])}

DOCUMENTS:
- Optimized resume (summary only): {optimized_resume[:600]}...
- Cover letter (summary only): {cover_letter[:400]}...

Your style:
- Be concise but detailed.
- Focus on risk, fit, growth, and strategy.
- Tell the user clearly if the role is a good move, a lateral move, or a bad idea.
- Suggest concrete actions (skills to learn, how to position themselves, what to ask in interviews).
"""
    }


def stream_coach_response(messages):
    # Server-side streaming from GPT-4o
    response_text = ""
    with client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                response_text += delta.content
                yield delta.content
    return response_text


# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(layout="wide")
st.title("🧠 Career AI Agent — ATS Pro + AI Coach")

# -------------------------
# LOAD SAVED PROFILE
# -------------------------
saved_profile = load_profile()

# -------------------------
# USER PROFILE INPUTS
# -------------------------
st.subheader("🧑‍💼 Your Profile")

user_skills_input = st.text_area(
    "Enter your skills (comma separated)",
    saved_profile["skills"] if saved_profile else "Active Directory, M365, VPN, troubleshooting, firewall"
)

user_preferred_locations = st.text_input(
    "Preferred locations (comma separated)",
    saved_profile["locations"] if saved_profile else "Halifax, Nova Scotia, Remote"
)

user_min_salary = st.number_input(
    "Minimum acceptable salary ($ per year)",
    min_value=0,
    value=saved_profile["min_salary"] if saved_profile else 60000
)

user_preferred_employers = st.text_input(
    "Preferred employer types (comma separated)",
    saved_profile["employers"] if saved_profile else "government, public sector, university"
)

user_skill_list = [s.strip().lower() for s in user_skills_input.split(",")]

CAREER_GOALS = {
    "target_roles": ["network administrator", "systems administrator", "it support"],
    "preferred_locations": [loc.strip().lower() for loc in user_preferred_locations.split(",")],
    "minimum_salary": user_min_salary,
    "preferred_employers": [e.strip().lower() for e in user_preferred_employers.split(",")],
    "avoid_roles": ["help desk", "senior", "manager"],
    "growth_skills": user_skill_list
}

# -------------------------
# JOB INPUTS
# -------------------------
st.subheader("🌐 Import Job Posting From URL")
job_url = st.text_input("Paste job posting URL (optional)")

st.subheader("📄 Job Posting")
job_title = st.text_input("Job Title")
job_desc = st.text_area("Job Description")
company = st.text_input("Company (optional)", "Public Sector")

# If URL provided, override job_desc
if job_url:
    st.info("Fetching job description from webpage...")
    job_desc = fetch_job_from_url(job_url)
    st.success("Job description loaded from webpage!")

# -------------------------
# ANALYZE BUTTON
# -------------------------
if st.button("Analyze Job"):

    save_profile({
        "skills": user_skills_input,
        "locations": user_preferred_locations,
        "min_salary": user_min_salary,
        "employers": user_preferred_employers
    })

    job_info = {
        "title": job_title,
        "location": extract_location(job_desc),
        "salary": extract_salary(job_desc),
        "employer": extract_employer(job_desc),
        "skills": extract_skills(job_desc)
    }

    match_score, matched_skills, missing_skills = analyze_match(user_skill_list, job_desc)
    optimized_resume = optimize_resume(user_skill_list, matched_skills, missing_skills, job_title)
    cover_letter = generate_cover_letter(job_title, company, matched_skills, missing_skills)
    offer_score, offer_level = offer_probability(match_score, job_desc)
    advice = compare_to_goals(job_info, CAREER_GOALS)
    job_summary = generate_job_summary(job_desc)

    tab_profile, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👤 Your Profile",
        "📊 Match Analysis",
        "🧠 Skills Extracted",
        "📍 Job Details",
        "📄 Optimized Resume",
        "✉️ Cover Letter",
        "🎯 Career Advice",
        "📝 Job Summary"
    ])

    with tab_profile:
        st.subheader("Your Skills")
        st.write(user_skill_list)

        st.subheader("Preferred Locations")
        st.write(CAREER_GOALS["preferred_locations"])

        st.subheader("Minimum Salary")
        st.write(f"${CAREER_GOALS['minimum_salary']}")

        st.subheader("Preferred Employers")
        st.write(CAREER_GOALS["preferred_employers"])

    with tab1:
        st.subheader("Match Score")
        st.write("Score:", match_score)
        st.write("Explanation:", explain_score(match_score))
        st.write("Offer Probability:", f"{offer_score}% — {offer_level}")
        st.write("Matched Skills:", matched_skills)
        st.write("Missing Skills:", missing_skills)

    with tab2:
        st.subheader("Skills Found in Job Description")
        st.write(job_info["skills"])

    with tab3:
        st.subheader("Job Details")
        st.write("Location:", job_info["location"])
        st.write("Salary:", job_info["salary"])
        st.write("Employer:", job_info["employer"])

    with tab4:
        st.subheader("Optimized Resume")
        st.text(optimized_resume)

    with tab5:
        st.subheader("Cover Letter")
        st.text(cover_letter)

    with tab6:
        st.subheader("Career Advice")
        for line in advice:
            st.write(line)

    with tab7:
        st.subheader("AI Job Summary")
        st.text(job_summary)

    # -------------------------
    # AI COACH — FULL-WIDTH BOTTOM CHAT
    # -------------------------
    st.markdown("---")
    st.subheader("🤖 AI Career Coach — Live Chat (Direct, Streaming)")

    if "coach_messages" not in st.session_state:
        st.session_state["coach_messages"] = []

    # Build system message once per analysis
    system_msg = build_coach_system_prompt(
        job_desc,
        job_info,
        user_skill_list,
        matched_skills,
        missing_skills,
        match_score,
        offer_score,
        offer_level,
        CAREER_GOALS,
        optimized_resume,
        cover_letter
    )

    # Ensure system message is first
    base_messages = [system_msg] + st.session_state["coach_messages"]

    # Chat history display (minimal style)
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["coach_messages"]:
            if msg["role"] == "user":
                st.markdown(f"<div style='text-align:right; background-color:#f0f0f0; padding:8px; border-radius:8px; margin:4px 0;'>{msg['content']}</div>", unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"<div style='text-align:left; background-color:#ffffff; padding:8px; border-radius:8px; margin:4px 0;'>{msg['content']}</div>", unsafe_allow_html=True)

    user_input = st.text_input("Ask the AI Coach about this opportunity, your fit, or your next steps:")

    col_send, _ = st.columns([1, 3])
    with col_send:
        if st.button("Send to AI Coach") and user_input.strip():
            # Add user message
            st.session_state["coach_messages"].append({"role": "user", "content": user_input})

            # Prepare messages with system + history
            messages = [system_msg] + st.session_state["coach_messages"]

            # Stream response
            placeholder = st.empty()
            full_response = ""
            for chunk in stream_coach_response(messages):
                full_response += chunk
                placeholder.markdown(
                    f"<div style='text-align:left; background-color:#ffffff; padding:8px; border-radius:8px; margin:4px 0;'>{full_response}</div>",
                    unsafe_allow_html=True
                )

            # Save assistant message
            st.session_state["coach_messages"].append({"role": "assistant", "content": full_response})

            # Rerun to show full history cleanly
            st.experimental_rerun()

else:
    st.info("Fill in the job details and click 'Analyze Job' to unlock the AI Coach chat at the bottom.")
