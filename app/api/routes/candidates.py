import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.vector_store import semantic_search_candidates
from app.database.session import get_db
from app.models.sql_models import CandidateORM
from app.schemas.candidate import (
    CandidateApplicationRequest,
    CandidateEvaluationResponse,
    SlotConfirmationRequest,
    InterviewEvaluationRequest,
    FinalDossierResponse,
    PipelineStatus
)
from app.agents.graph import recruitment_graph
from app.integrations.calendar_api import book_calendar_slot

router = APIRouter(prefix="/api/v1/candidates", tags=["Agentic Recruitment Pipeline"])

@router.post("/apply", response_model=CandidateEvaluationResponse)
async def apply_and_evaluate(payload: CandidateApplicationRequest, db: Session = Depends(get_db)):
    """
    Runs the LangGraph Multi-Agent Swarm and persists the complete state into the SQL Database.
    """
    candidate_id = f"CAND-{uuid.uuid4().hex[:6].upper()}"

    initial_state = {
        "candidate_id": candidate_id,
        "anonymized_id": "",
        "full_name": payload.full_name,
        "email": payload.email,
        "job_id": payload.job_id,
        "job_description": payload.job_description,
        "raw_resume_text": payload.resume_text,
        "scrubbed_resume_text": "",
        "extracted_skills": [],
        "years_of_experience": 0.0,
        "missing_skills": [],
        "match_score": 0.0,
        "screening_feedback": "",
        "technical_questions": [],
        "assessment_score": None,
        "proposed_slots": [],
        "confirmed_slot": None,
        "meeting_link": None,
        "email_sent": False,
        "latest_email_body": None,
        "status": PipelineStatus.NEW.value,
        "audit_log": [f"[API Gateway] Application received for {payload.job_id} ({candidate_id})."]
    }

    # Execute LangGraph Swarm
    final_state = await recruitment_graph.ainvoke(initial_state)

    # Persist into SQL Database via SQLAlchemy ORM
    db_candidate = CandidateORM(
        candidate_id=final_state["candidate_id"],
        anonymized_id=final_state["anonymized_id"],
        full_name=final_state["full_name"],
        email=final_state["email"],
        job_id=final_state["job_id"],
        job_description=final_state["job_description"],
        raw_resume_text=final_state["raw_resume_text"],
        scrubbed_resume_text=final_state["scrubbed_resume_text"],
        extracted_skills=final_state["extracted_skills"],
        missing_skills=final_state["missing_skills"],
        years_of_experience=final_state["years_of_experience"],
        match_score=final_state["match_score"],
        screening_feedback=final_state["screening_feedback"],
        technical_questions=final_state["technical_questions"],
        proposed_slots=final_state["proposed_slots"],
        email_sent=final_state["email_sent"],
        latest_email_body=final_state["latest_email_body"],
        status=final_state["status"],
        audit_log=final_state["audit_log"]
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)

    return CandidateEvaluationResponse(
        candidate_id=db_candidate.candidate_id,
        anonymized_id=db_candidate.anonymized_id,
        status=db_candidate.status,
        extracted_skills=db_candidate.extracted_skills,
        missing_skills=db_candidate.missing_skills,
        match_score=db_candidate.match_score,
        screening_feedback=db_candidate.screening_feedback,
        technical_questions=db_candidate.technical_questions,
        proposed_slots=db_candidate.proposed_slots,
        email_dispatched=db_candidate.email_sent,
        email_preview=db_candidate.latest_email_body,
        audit_log=db_candidate.audit_log
    )

@router.post("/confirm-slot")
async def confirm_interview_slot(payload: SlotConfirmationRequest, db: Session = Depends(get_db)):
    """
    Verifies candidate in SQL DB, locks the slot in the BookedSlotORM table,
    and updates the candidate record with the confirmed time and Google Meet link.
    """
    candidate = db.query(CandidateORM).filter(
        CandidateORM.candidate_id == payload.candidate_id.strip()
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate ID '{payload.candidate_id}' not found in DB.")

    if candidate.status == PipelineStatus.REJECTED.value:
        raise HTTPException(status_code=400, detail="Cannot schedule interview for a rejected candidate.")

    booking_result = book_calendar_slot(
        candidate_id=candidate.candidate_id,
        candidate_email=candidate.email,
        selected_slot=payload.selected_slot,
        interviewer_email=payload.interviewer_email
    )

    if booking_result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=booking_result["message"])

    # Update ORM columns (Reassigning list so SQLAlchemy detects JSON mutation)
    candidate.confirmed_slot = payload.selected_slot
    candidate.meeting_link = booking_result["meeting_link"]
    updated_logs = list(candidate.audit_log)
    updated_logs.append(
        f"[Coordinator Agent] Locked DB slot '{payload.selected_slot}' & generated link: {booking_result['meeting_link']}"
    )
    candidate.audit_log = updated_logs

    db.commit()
    db.refresh(candidate)

    return {
        "candidate_id": candidate.candidate_id,
        "status": "slot_locked",
        "confirmed_slot": candidate.confirmed_slot,
        "interviewer_email": payload.interviewer_email,
        "meeting_link": candidate.meeting_link,
        "audit_log": candidate.audit_log
    }

@router.post("/evaluate-interview", response_model=FinalDossierResponse)
async def evaluate_post_interview(payload: InterviewEvaluationRequest, db: Session = Depends(get_db)):
    """
    Evaluates post-interview transcript, stores final composite score and verdict in SQL DB,
    and dispatches the final Offer or Rejection email.
    """
    candidate = db.query(CandidateORM).filter(
        CandidateORM.candidate_id == payload.candidate_id.strip()
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate ID '{payload.candidate_id}' not found in DB.")

    transcript_lower = payload.interview_transcript.lower()
    positive_signals = ["clearly", "deep", "strong", "excellent", "good", "well", "solid", "great"]
    signal_hits = sum(1 for word in positive_signals if word in transcript_lower)

    interview_score = min(round((payload.interviewer_rating * 8.5) + (signal_hits * 3.0), 2), 100.0)
    resume_score = candidate.match_score
    composite_score = round((resume_score * 0.4) + (interview_score * 0.6), 2)

    if composite_score >= 80.0:
        recommendation = "STRONG_HIRE"
        summary = f"Exceptional technical depth during interview ({interview_score}%). Cleared gap probes smoothly."
        email_body = (
            f"Subject: Official Offer Letter for {candidate.job_id} - TalentAI\n"
            f"Hi {candidate.full_name},\n\nWe were thoroughly impressed by your interview! "
            f"Your composite evaluation score is {composite_score}/100 ({recommendation}). "
            f"We are thrilled to extend an official offer to join our engineering team!"
        )
    elif composite_score >= 68.0:
        recommendation = "HIRE"
        summary = f"Solid overall performance ({composite_score}%). Meets engineering bar for {candidate.job_id}."
        email_body = (
            f"Subject: Next Steps & Offer Details for {candidate.job_id}\n"
            f"Hi {candidate.full_name},\n\nThank you for a great technical discussion! "
            f"We are pleased to move forward with an offer for {candidate.job_id}."
        )
    else:
        recommendation = "NO_HIRE"
        summary = f"Composite score ({composite_score}%) fell below the hiring bar of 68.0%."
        email_body = (
            f"Subject: Update on your interview for {candidate.job_id}\n"
            f"Hi {candidate.full_name},\n\nThank you for taking the time to interview with us. "
            f"While we enjoyed learning about your background, we have decided to pursue other candidates at this stage."
        )

    candidate.status = PipelineStatus.EVALUATED.value
    candidate.interview_score = interview_score
    candidate.assessment_score = composite_score
    candidate.hiring_recommendation = recommendation
    candidate.evaluation_summary = summary
    candidate.latest_email_body = email_body

    updated_logs = list(candidate.audit_log)
    updated_logs.append(
        f"[Debrief Agent] Persisted final evaluation to DB. Interview: {interview_score}%, "
        f"Composite: {composite_score}%, Verdict: {recommendation}."
    )
    candidate.audit_log = updated_logs

    db.commit()
    db.refresh(candidate)

    return FinalDossierResponse(
        candidate_id=candidate.candidate_id,
        full_name=candidate.full_name,
        status=candidate.status,
        resume_match_score=resume_score,
        interview_score=interview_score,
        final_composite_score=composite_score,
        hiring_recommendation=recommendation,
        evaluation_summary=summary,
        final_email_preview=email_body,
        audit_log=candidate.audit_log
    )

@router.get("/")
async def list_all_candidates(db: Session = Depends(get_db)):
    """Fetches all candidates ordered by newest first directly from the SQL database."""
    candidates = db.query(CandidateORM).order_by(CandidateORM.created_at.desc()).all()
    return candidates

@router.get("/semantic-search")
async def search_resumes_in_qdrant(query: str = "Python FastAPI LangGraph", limit: int = 5):
    """Performs cosine similarity vector search in Qdrant across all anonymized resumes."""
    return semantic_search_candidates(query_text=query, limit=limit)