from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple GET health check endpoint for monitoring app status."""
    return {"status": "ok"}
