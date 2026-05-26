from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "warroom-ai-api", "version": "0.1.0"}
