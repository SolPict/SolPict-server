import os
from fastapi import Request, HTTPException
import redis.asyncio as redis

redis_client = redis.from_url(
    os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True
)


async def check_device_request_limit(
    request: Request, api_name: str, max_calls: int = 10
):
    device_id = request.headers.get("Device-Id")
    if not device_id:
        raise HTTPException(status_code=400, detail="Device-Id header가 필요합니다.")

    redis_key = f"device_limit:{api_name}:{device_id}"

    current_count = await redis_client.get(redis_key)
    current_count = int(current_count) if current_count else 0

    if current_count >= max_calls:
        raise HTTPException(
            status_code=429, detail=f"{api_name} API 호출 제한을 초과했습니다."
        )

    pipeline = redis_client.pipeline()
    pipeline.incr(redis_key)

    if current_count == 0:
        pipeline.expire(redis_key, 86400)

    await pipeline.execute()
