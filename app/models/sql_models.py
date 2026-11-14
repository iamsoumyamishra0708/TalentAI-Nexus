from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Text, JSON, DateTime, Integer, UniqueConstraint
from app.database.session import Base

class CandidateORM(Base):
    """Relational table storing the complete lifecycle and agent outputs for each candidate."""
    __tablename__ = "candidates"

    candidate_id = Column(String(50), primary_key=True, index=True)
    anonymized_id = Column(String(50), unique=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    job_id = Column(String(50), nullable=False, index=True)
    job_description = Column(Text, nullable=False)
    raw_resume_text = Column(Text, nullable=False)
    scrubbed_resume_text = Column(Text, nullable=True)

    # Structured Agent Outputs (Stored natively as JSON arrays)
    extracted_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    years_of_experience = Column(Float, default=0.0)

    # Screening & Assessment Metrics
    match_score = Column(Float, default=0.0)
    screening_feedback = Column(Text, nullable=True)
    technical_questions = Column(JSON, default=list)

    # Scheduling & Coordinator Data
    proposed_slots = Column(JSON, default=list)
    confirmed_slot = Column(String(100), nullable=True)
    meeting_link = Column(String(255), nullable=True)
    email_sent = Column(Boolean, default=False)
    latest_email_body = Column(Text, nullable=True)

    # Post-Interview Debrief & Final Decision
    interview_score = Column(Float, nullable=True)
    assessment_score = Column(Float, nullable=True) # Composite Score
    hiring_recommendation = Column(String(50), nullable=True)
    evaluation_summary = Column(Text, nullable=True)

    # Pipeline Status & Explainable AI Audit Trail
    status = Column(String(50), default="new", index=True)
    audit_log = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class BookedSlotORM(Base):
    """ACID-compliant table preventing double-booking of interviewer calendar slots."""
    __tablename__ = "booked_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interviewer_email = Column(String(150), nullable=False, index=True)
    slot_time = Column(String(100), nullable=False)
    candidate_id = Column(String(50), nullable=False)
    meeting_link = Column(String(255), nullable=False)
    booked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Guarantees two candidates can NEVER lock the same interviewer + slot_time
    __table_args__ = (
        UniqueConstraint("interviewer_email", "slot_time", name="uq_interviewer_slot"),
    )