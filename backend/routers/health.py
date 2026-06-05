from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "persona": "Gundumalla Sthana Sriharsha"}
