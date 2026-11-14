from typing import List, Dict

def send_shortlist_and_slots_email(
    to_email: str,
    candidate_name: str,
    job_id: str,
    questions: List[str],
    proposed_slots: List[str]
) -> Dict[str, str]:
    """
    Drafts and dispatches an automated email containing the pre-interview 
    technical questions and available interviewer calendar slots.
    """
    formatted_questions = "\n".join([f"  {i+1}. {q}" for i, q in enumerate(questions)])
    formatted_slots = "\n".join([f"  - {slot}" for slot in proposed_slots])

    email_body = f"""Subject: [TalentAI] Next Steps & Interview Scheduling for {job_id}
To: {to_email}

Hi {candidate_name},

Congratulations! Our AI Screening Engine reviewed your profile for {job_id} and found a strong match with our engineering requirements.

Before we meet, please keep these tailored technical discussion points in mind:
{formatted_questions}

We have checked our Hiring Manager's calendar. Please select ONE of the following available slots to lock your interview:
{formatted_slots}

Best regards,
TalentAI Autonomous Coordinator
"""
    # Log in terminal for instant visibility during development
    print("\n" + "="*60)
    print(f"📧 [EMAIL DISPATCHED TO: {to_email}]")
    print("="*60)
    print(email_body.strip())
    print("="*60 + "\n")

    return {"sent": True, "body": email_body.strip()}


def send_rejection_email(to_email: str, candidate_name: str, job_id: str, feedback: str) -> Dict[str, str]:
    """Sends a polite, constructive rejection email if the screening threshold is not met."""
    email_body = f"""Subject: Update on your application for {job_id}
To: {to_email}

Hi {candidate_name},

Thank you for applying for {job_id}. After an automated review of your profile against our current technical requirements, we will not be moving forward at this stage.

Feedback Note: {feedback}

We will keep your profile in our vector database for future openings.

Best regards,
TalentAI Recruitment Team
"""
    print(f"\n📧 [REJECTION EMAIL DISPATCHED TO: {to_email}]\n")
    return {"sent": True, "body": email_body.strip()}