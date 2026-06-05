from fastapi import APIRouter
from pydantic import BaseModel
from services.calcom import get_available_slots, book_slot

router = APIRouter()

class BookingRequest(BaseModel):
    name: str
    email: str
    start_time: str  # ISO 8601
    notes: str = ""

@router.get("/availability")
def availability(days: int = 7):
    slots = get_available_slots(days_ahead=days)
    return {"slots": slots}

@router.post("/book")
def book(req: BookingRequest):
    result = book_slot(req.name, req.email, req.start_time, req.notes)
    return result
