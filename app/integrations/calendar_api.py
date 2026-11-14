from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.exc import IntegrityError
from app.database.session import SessionLocal
from app.models.sql_models import BookedSlotORM

def get_interviewer_free_slots(interviewer_email: str = "hiring.manager@talentai.com", num_slots: int = 3) -> List[str]:
    """
    Queries the SQL database for already booked slots for the interviewer,
    filters them out, and returns the next available 45-min working slots.
    """
    db = SessionLocal()
    try:
        booked_rows = db.query(BookedSlotORM.slot_time).filter(
            BookedSlotORM.interviewer_email == interviewer_email
        ).all()
        booked_set = {row[0] for row in booked_rows}
    finally:
        db.close()

    base_date = datetime.now() + timedelta(days=1)
    standard_working_slots = ["11:00 IST", "14:00 IST", "16:30 IST"]
    available_slots = []

    for day_offset in range(1, 6):
        target_date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for time_str in standard_working_slots:
            slot_candidate = f"{target_date} {time_str}"
            if slot_candidate not in booked_set:
                available_slots.append(slot_candidate)
            if len(available_slots) == num_slots:
                return available_slots

    return available_slots


def book_calendar_slot(
    candidate_id: str,
    candidate_email: str,
    selected_slot: str,
    interviewer_email: str = "hiring.manager@talentai.com"
) -> Dict[str, str]:
    """
    Uses database ACID transactions and UniqueConstraint to lock a slot.
    If another candidate booked it milliseconds ago, IntegrityError catches the collision.
    """
    db = SessionLocal()
    try:
        meet_code = candidate_id.lower().replace("-", "")[:8]
        meeting_link = f"https://meet.google.com/tal-{meet_code}-ai"

        new_booking = BookedSlotORM(
            interviewer_email=interviewer_email,
            slot_time=selected_slot,
            candidate_id=candidate_id,
            meeting_link=meeting_link
        )
        db.add(new_booking)
        db.commit()

        return {
            "status": "confirmed",
            "message": f"Slot locked in database for {selected_slot}",
            "meeting_link": meeting_link
        }
    except IntegrityError:
        db.rollback()
        return {
            "status": "conflict",
            "message": f"Slot '{selected_slot}' for {interviewer_email} is already booked in the database.",
            "meeting_link": ""
        }
    finally:
        db.close()