import logging
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts using SequenceMatcher."""
    return SequenceMatcher(None, text1, text2).ratio()

def screen_resume(resume: dict, job_description: dict):
    """Screen a resume against a job description using text matching."""
    # Validate input
    if not resume.get("skills") or not job_description.get("skills"):
        logging.info("Invalid input: Missing skills in resume or job description.")
        return {
            "score": 0,
            "matched_skills": []
        }

    # Convert skills to lowercase for case-insensitive matching
    resume_skills = [skill.lower() for skill in resume.get("skills", [])]
    job_skills = [skill.lower() for skill in job_description.get("skills", [])]
    
    # Calculate skill match
    matched_skills = []
    for job_skill in job_skills:
        for resume_skill in resume_skills:
            if job_skill in resume_skill or resume_skill in job_skill:
                matched_skills.append(resume_skill)
    
    # Calculate score based on matched skills
    score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0
    
    # Add summary matching if available
    if resume.get("summary") and job_description.get("description"):
        summary_similarity = calculate_similarity(
            resume["summary"].lower(),
            job_description["description"].lower()
        )
        score = (score + (summary_similarity * 100)) / 2

    response = {
        "score": round(score, 2),
        "matched_skills": list(set(matched_skills))  # Remove duplicates
    }

    logging.info(f"Screening response: {response}")
    return response