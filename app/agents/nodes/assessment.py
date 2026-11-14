from typing import Dict, List
from app.agents.state import CandidateState

QUESTION_BANK = {
    "python": "How does Python's asyncio event loop handle concurrent I/O-bound tasks vs CPU-bound tasks?",
    "fastapi": "How do you design non-blocking background tasks and dependency injection in FastAPI?",
    "langgraph": "How do you manage state persistence, cyclic routing, and human-in-the-loop checkpoints in LangGraph?",
    "qdrant": "Explain how hybrid search (Dense Vectors + Sparse BM25) improves retrieval accuracy in Qdrant.",
    "docker": "How do multi-stage Docker builds optimize container size and security for ML microservices?",
    "postgresql": "How do you prevent race conditions when two users try to book the same interview slot in PostgreSQL?"
}

def assessment_node(state: CandidateState) -> Dict:
    """
    Dynamically generates tailored technical questions based on the candidate's
    strongest skills and any missing skill gaps identified during screening.
    """
    questions: List[str] = []
    candidate_skills = [s.lower() for s in state["extracted_skills"]]

    # 1. Pick depth verification questions from skills they claim to know
    for skill in candidate_skills:
        if skill in QUESTION_BANK and len(questions) < 2:
            questions.append(QUESTION_BANK[skill])

    # 2. If they had a missing skill in the JD, add a probe question for that gap
    for missing in state["missing_skills"]:
        m_lower = missing.lower()
        if m_lower in QUESTION_BANK and len(questions) < 3:
            questions.append(f"[Gap Probe - {missing}] {QUESTION_BANK[m_lower]}")

    # 3. Fallback architecture question
    if len(questions) < 3:
        questions.append("Walk us through a production microservice or AI architecture you designed end-to-end.")

    log_entry = f"[Assessment Agent] Generated {len(questions)} tailored technical questions for {state['anonymized_id']}."

    return {
        "technical_questions": questions,
        "status": "assessment_sent",
        "audit_log": [log_entry]
    }