from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PipelineStatus(str, Enum):
    """Strict states a candidate can be in during the recruitment lifecycle."""
    NEW = "new"
    PARSED = "parsed"
    SCREENED = "screened"
    ASSESSMENT_SENT = "assessment_sent"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    EVALUATED = "evaluated"
    REJECTED = "rejected"

class CandidateApplicationRequest(BaseModel):
    """Input payload when a candidate applies via frontend or webhook."""
    full_name: str = Field(..., min_length=2, example="Aarav Sharma")
    email: str = Field(..., example="aarav.sharma@example.com")
    job_id: str = Field(..., example="JOB-AI-2026")
    job_description: str = Field(
        ..., 
        min_length=10,
        example="Looking for an AI Engineer skilled in Python, FastAPI, LangGraph, Qdrant, and Docker."
    )
    resume_text: str = Field(
        ..., 
        min_length=20,
        example="3+ years experience building agentic workflows with Python, FastAPI, LangGraph, and deploying on AWS."
    )

class SlotConfirmationRequest(BaseModel):
    """Payload when a candidate replies to pick an interview slot."""
    candidate_id: str = Field(..., example="CAND-A1B2C3")
    selected_slot: str = Field(..., example="2026-11-16 14:00 IST")
    interviewer_email: str = Field(default="hiring.manager@talentai.com")

class CandidateEvaluationResponse(BaseModel):
    """Structured output returned by the API after the Agent Swarm finishes execution."""
    candidate_id: str
    anonymized_id: str
    status: PipelineStatus
    extracted_skills: List[str]
    missing_skills: List[str]
    match_score: float = Field(..., ge=0.0, le=100.0)
    screening_feedback: str
    technical_questions: List[str]
    proposed_slots: List[str] = Field(default_factory=list)
    email_dispatched: bool
    email_preview: Optional[str] = None
    audit_log: List[str]

    class Config:
        populate_by_name = True

class InterviewEvaluationRequest(BaseModel):
    """Payload submitted after the interview is completed (Transcript or Interviewer Notes)."""
    candidate_id: str = Field(..., example="CAND-A1B2C3")
    interview_transcript: str = Field(
        ...,
        min_length=20,
        example="Candidate explained Python asyncio event loop clearly, demonstrated deep knowledge of FastAPI dependency injection, and understood Qdrant hybrid search tradeoffs well. Strong communication."
    )
    interviewer_rating: float = Field(default=8.5, ge=1.0, le=10.0, example=8.5)

class FinalDossierResponse(BaseModel):
    """Final 360-degree evaluation scorecard and hiring decision."""
    candidate_id: str
    full_name: str
    status: str
    resume_match_score: float
    interview_score: float
    final_composite_score: float
    hiring_recommendation: str  # "STRONG_HIRE", "HIRE", "NO_HIRE"
    evaluation_summary: str
    final_email_preview: str
    audit_log: List[str]