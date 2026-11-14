from typing import Dict
from app.agents.state import CandidateState
from app.integrations.calendar_api import get_interviewer_free_slots
from app.integrations.email_service import send_shortlist_and_slots_email, send_rejection_email

def coordinator_node(state: CandidateState) -> Dict:
    """
    Handles automated calendar slot discovery and candidate email outreach
    based on whether the candidate passed or failed the screening threshold.
    """
    if state["match_score"] >= 65.0:
        # 1. Check interviewer's calendar for free slots
        free_slots = get_interviewer_free_slots(num_slots=3)

        # 2. Send automated email with technical questions and available slots
        email_result = send_shortlist_and_slots_email(
            to_email=state["email"],
            candidate_name=state["full_name"],
            job_id=state["job_id"],
            questions=state["technical_questions"],
            proposed_slots=free_slots
        )

        log_entry = (
            f"[Coordinator Agent] Fetched {len(free_slots)} open interviewer slots {free_slots} "
            f"and dispatched scheduling email to {state['email']}."
        )

        return {
            "proposed_slots": free_slots,
            "email_sent": email_result["sent"],
            "latest_email_body": email_result["body"],
            "status": "interview_scheduled",
            "audit_log": [log_entry]
        }
    else:
        # Candidate did not meet threshold -> Send automated rejection email
        email_result = send_rejection_email(
            to_email=state["email"],
            candidate_name=state["full_name"],
            job_id=state["job_id"],
            feedback=state["screening_feedback"]
        )

        log_entry = f"[Coordinator Agent] Candidate below threshold. Dispatched polite rejection email to {state['email']}."

        return {
            "proposed_slots": [],
            "email_sent": email_result["sent"],
            "latest_email_body": email_result["body"],
            "status": "rejected",
            "audit_log": [log_entry]
        }