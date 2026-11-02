from fastapi import APIRouter

router = APIRouter(tags=["salud"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
