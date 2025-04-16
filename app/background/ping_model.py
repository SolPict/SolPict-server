import asyncio
import requests
import os

HUGGINGFACE_PING_URL = os.getenv("HUGGING_FACE_API_URL")
API_KEY = os.getenv("HUGGING_FACE_API_KEY")


def ping_huggingface_model():
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        data = {"inputs": "ping"}
        requests.post(HUGGINGFACE_PING_URL, headers=headers, json=data)
    except Exception as error:
        print(f"HuggingFace 요청에 실패 했습니다. {error}")


async def start_ping_loop():
    while True:
        await asyncio.to_thread(ping_huggingface_model)
        await asyncio.sleep(300)
