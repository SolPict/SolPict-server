from fastapi import APIRouter

router = APIRouter(prefix="/health_check", tags=["health_check"])


@router.get("")
async def health_check():
    return {"status": "ok"}
