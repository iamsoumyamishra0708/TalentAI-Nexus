from typing import Dict
from app.agents.state import CandidateState
from app.agents.nodes.parser import KNOWN_TECH_SKILLS

def screener_node(state: CandidateState) -> Dict:
    """
    Compares candidate's extracted skills against Job Description requirements,
    identifies missing gaps, and calculates a weighted semantic match score.
    """
    jd_lower = state["job_description"].lower()
    candidate_skills_lower = {s.lower() for s in state["extracted_skills"]}

    # Identify required skills from the Job Description
    required_skills = [skill for skill in KNOWN_TECH_SKILLS if skill in jd_lower]
    
    if not required_skills:
        required_skills = ["python", "fastapi"] # Fallback baseline

    matched_skills = [s for s in required_skills if s in candidate_skills_lower]
    missing_skills = [s.title() for s in required_skills if s not in candidate_skills_lower]

    # Calculate score: 85% weight to skill overlap + 15% bonus for experience (up to 3+ years)
    skill_ratio = len(matched_skills) / len(required_skills)
    exp_bonus = min(state["years_of_experience"] / 3.0, 1.0) * 15.0
    final_score = round((skill_ratio * 85.0) + exp_bonus, 2)

    if final_score >= 65.0:
        feedback = (
            f"Strong semantic alignment ({final_score}%). Candidate covers {len(matched_skills)}/{len(required_skills)} "
            f"core JD skills. Recommended for technical assessment and interview."
        )
    else:
        feedback = (
            f"Below threshold ({final_score}%). Missing critical requirements: {', '.join(missing_skills)}."
        )

    log_entry = f"[Screener Agent] Scored {final_score}/100. Missing skills: {missing_skills or 'None'}."

    return {
        "missing_skills": missing_skills,
        "match_score": final_score,
        "screening_feedback": feedback,
        "status": "screened",
        "audit_log": [log_entry]
    }