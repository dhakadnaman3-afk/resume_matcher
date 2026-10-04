import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY")
)


def extract_skills(text: str) -> list[str]:
    prompt = f"""
    Extract only the technical skills, tools, and technologies mentioned in the text below.
    Return them as a comma-separated list, nothing else. No explanation, no numbering.

    Text:
    {text}
    """
    response = llm.invoke(prompt)
    skills_text = response.content
    skills_list = [skill.strip() for skill in skills_text.split(",")]
    return skills_list




def compare_skills(resume_skills: list[str], jd_skills: list[str]) -> dict:
    # case-insensitive comparison ke liye lowercase set banate hain
    resume_set = set(skill.lower().strip() for skill in resume_skills)
    jd_set = set(skill.lower().strip() for skill in jd_skills)

    matched = resume_set & jd_set        # intersection — dono me common
    missing = jd_set - resume_set        # JD me hai, resume me nahi

    match_percentage = round((len(matched) / len(jd_set)) * 100, 2) if jd_set else 0

    return {
        "matched_skills": list(matched),
        "missing_skills": list(missing),
        "match_percentage": match_percentage
    }




def generate_advice(missing_skills: list[str]) -> str:
    if not missing_skills:
        return "Great! Your resume already covers all the required skills."

    skills_text = ", ".join(missing_skills)
    prompt = f"""
    A candidate is missing the following skills required for a job: {skills_text}.
    Give a short, encouraging, 2-3 sentence suggestion on how they can quickly 
    upskill or highlight related experience to bridge this gap.
    """
    response = llm.invoke(prompt)
    return response.content
