import asyncio
import requests
import os


def ping_huggingface_model():
    try:
        HUGGINGFACE_PING_URL = os.getenv("HUGGING_FACE_API_URL")
        API_KEY = os.getenv("HUGGING_FACE_API_KEY")

        headers = {"Authorization": f"Bearer {API_KEY}"}
        data = {"inputs": "ping"}
        if not HUGGINGFACE_PING_URL:
            print("HuggingFace URL 환경변수가 설정되지 않았습니다.")
            return

        requests.post(HUGGINGFACE_PING_URL, headers=headers, json=data)
    except Exception as error:
        print(f"HuggingFace 요청에 실패 했습니다. {error}")


async def start_ping_loop():
    while True:
        await asyncio.to_thread(ping_huggingface_model)
        await asyncio.sleep(200)
