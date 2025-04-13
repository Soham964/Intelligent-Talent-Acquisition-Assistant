from datetime import datetime, timedelta
from typing import List, Dict

# In-memory storage for interview slots and bookings
_available_slots = [
    "09:00 AM", "10:00 AM", "11:00 AM",
    "02:00 PM", "03:00 PM", "04:00 PM"
]

_booked_slots: Dict[str, Dict] = {}

def get_available_slots() -> List[str]:
    """Get list of available interview slots."""
    return [slot for slot in _available_slots if slot not in _booked_slots]

def get_booked_slots() -> Dict[str, Dict]:
    """Get dictionary of booked interview slots."""
    return _booked_slots

def schedule_interview(candidate_name: str, time_slot: str) -> Dict:
    """Schedule an interview for a candidate at the specified time slot."""
    if time_slot not in _available_slots:
        raise ValueError("Invalid time slot")
    
    if time_slot in _booked_slots:
        raise ValueError("Time slot already booked")
    
    # Book the slot
    _booked_slots[time_slot] = {
        "candidate_name": candidate_name,
        "booking_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "scheduled"
    }
    
    return {
        "candidate_name": candidate_name,
        "interview_time": time_slot,
        "status": "Interview scheduled"
    }