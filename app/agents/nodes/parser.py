import re
import uuid
from typing import Dict
from app.agents.state import CandidateState
from app.database.vector_store import index_candidate_resume

KNOWN_TECH_SKILLS = [
    "python", "fastapi", "flask", "django", "langgraph", "langchain",
    "qdrant", "postgresql", "mongodb", "redis", "docker", "aws",
    "kubernetes", "pydantic", "sqlalchemy", "react", "nextjs", "machine learning", "genai"
]

def parser_node(state: CandidateState) -> Dict:
    """
    1. Redacts PII (Name & Email) to ensure zero-bias downstream evaluation.
    2. Extracts technical skills and estimates years of experience.
    3. Indexes the scrubbed resume into the Qdrant Vector Store.
    """
    raw_text = state["raw_resume_text"]
    anonymized_id = f"ANON-{uuid.uuid4().hex[:6].upper()}"

    scrubbed_text = re.sub(re.escape(state["full_name"]), f"[{anonymized_id}]", raw_text, flags=re.IGNORECASE)
    scrubbed_text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", scrubbed_text)

    resume_lower = raw_text.lower()
    extracted_skills = [skill.upper() if len(skill) <= 3 else skill.title() 
                        for skill in KNOWN_TECH_SKILLS if skill in resume_lower]

    exp_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?", resume_lower)
    years_exp = float(exp_match.group(1)) if exp_match else 1.0

    # Index into Qdrant Vector DB
    index_candidate_resume(
        candidate_id=state["candidate_id"],
        anonymized_id=anonymized_id,
        job_id=state["job_id"],
        scrubbed_text=scrubbed_text,
        skills=extracted_skills
    )

    log_entry = (
        f"[Parser Agent] Masked PII as {anonymized_id}, indexed embeddings in Qdrant, "
        f"and extracted {len(extracted_skills)} skills ({', '.join(extracted_skills)})."
    )

    return {
        "anonymized_id": anonymized_id,
        "scrubbed_resume_text": scrubbed_text,
        "extracted_skills": extracted_skills,
        "years_of_experience": years_exp,
        "status": "parsed",
        "audit_log": [log_entry]
    }