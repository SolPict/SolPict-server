import os
from fastapi import Request, HTTPException
import redis.asyncio as redis

redis_client = redis.from_url(
    os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True
)


async def check_rate_limit(request: Request, api_name: str, limit_time_sec: int = 20):
    device_id = request.headers.get("Device-Id")
    if not device_id:
        raise HTTPException(status_code=400, detail="Device-Id header가 필요합니다.")

    redis_key = f"rate_limit:{api_name}:{device_id}"

    exists = await redis_client.exists(redis_key)
    if exists:
        raise HTTPException(
            status_code=429, detail=f"{api_name} API가 너무 빠르게 호출되었습니다."
        )

    await redis_client.set(redis_key, 1, ex=limit_time_sec)
