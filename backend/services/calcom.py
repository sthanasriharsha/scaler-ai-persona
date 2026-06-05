import os
import httpx
from datetime import datetime, timedelta

CALCOM_BASE = "https://api.cal.com/v1"
API_KEY = os.getenv("CALCOM_API_KEY", "")
EVENT_TYPE_ID = os.getenv("CALCOM_EVENT_TYPE_ID", "")

def get_available_slots(days_ahead: int = 7) -> list[dict]:
    """Fetch available slots from Cal.com for the next N days."""
    start = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
    try:
        resp = httpx.get(
            f"{CALCOM_BASE}/slots",
            params={
                "apiKey": API_KEY,
                "eventTypeId": EVENT_TYPE_ID,
                "startTime": start,
                "endTime": end,
                "timeZone": "Asia/Kolkata",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        slots = []
        for date, times in data.get("slots", {}).items():
            for t in times:
                slots.append({"date": date, "time": t.get("time", ""), "iso": t.get("time", "")})
        return slots[:10]
    except Exception as e:
        return [{"error": str(e)}]

def book_slot(name: str, email: str, start_time: str, notes: str = "") -> dict:
    """Book a slot on Cal.com."""
    try:
        resp = httpx.post(
            f"{CALCOM_BASE}/bookings",
            params={"apiKey": API_KEY},
            json={
                "eventTypeId": int(EVENT_TYPE_ID),
                "start": start_time,
                "responses": {
                    "name": name,
                    "email": email,
                    "notes": notes or "Booked via Sriharsha AI Persona",
                },
                "timeZone": "Asia/Kolkata",
                "language": "en",
                "metadata": {},
            },
            timeout=10,
        )
        resp.raise_for_status()
        booking = resp.json()
        return {
            "success": True,
            "booking_id": booking.get("uid", ""),
            "title": booking.get("title", "Interview with Sriharsha"),
            "start": booking.get("startTime", start_time),
            "join_url": booking.get("metadata", {}).get("videoCallUrl", ""),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
