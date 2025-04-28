import requests
import os
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
HUGGING_FACE_API_URL = os.getenv("HUGGING_FACE_API_URL")

if not HUGGING_FACE_API_KEY or not HUGGING_FACE_API_URL:
    raise EnvironmentError(
        "환경변수 HUGGING_FACE_API_KEY 또는 HUGGING_FACE_API_URL이 설정되지 않았습니다."
    )

HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
    "Content-Type": "application/json",
}


def request_huggingface(en_problem: str) -> Optional[str]:
    try:
        payload = {
            "inputs": en_problem,
            "parameters": {
                "max_new_tokens": 500,
                "return_full_text": False,
            },
        }

        response = requests.post(HUGGING_FACE_API_URL, headers=HEADERS, json=payload)

        if response.status_code == 503:
            print("Hugging Face 서버가 일시적으로 응답하지 않습니다.")
            return 503
        elif response.status_code == 504:
            print("Hugging Face 요청이 타임아웃되었습니다.")
            return 504
        elif response.status_code == 401:
            raise Exception("인증 실패: API 키를 확인하세요.")
        elif response.status_code != 200:
            raise Exception(f"요청 실패: {response.status_code}, {response.text}")

        response_data = response.json()

        if isinstance(response_data, dict) and "generated_text" in response_data:
            return response_data["generated_text"]
        elif (
            isinstance(response_data, list)
            and len(response_data) > 0
            and "generated_text" in response_data[0]
        ):
            return response_data[0]["generated_text"]
        else:
            raise Exception(f"예상치 못한 응답 형식입니다: {response_data}")

    except Exception as error:
        print(f"Hugging Face 요청 실패입니다: {error}")
        return None


async def request_huggingface_async(en_problem: str) -> Optional[str]:
    return await asyncio.to_thread(request_huggingface, en_problem)
