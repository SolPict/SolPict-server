import asyncio
import os
from typing import Optional
from huggingface_hub import InferenceClient


def request_huggingface(en_problem: str) -> Optional[str]:
    try:
        client = InferenceClient(api_key=os.getenv("HUGGING_FACE_API_KEY"))
        messages = [{"role": "user", "content": en_problem}]

        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-Math-1.5B-Instruct",
            messages=messages,
            max_tokens=500,
        )

        return completion.choices[0].message["content"]

    except Exception as error:
        error_str = str(error)
        if "503" in error_str:
            print("Hugging Face 서버가 일시적으로 응답하지 않습니다.")
            return 503
        elif "504" in error_str:
            print("Hugging Face 요청이 타임아웃되었습니다.")
            return 504
        else:
            print(f"Hugging Face 요청 실패입니다. {error_str}")
        return None


async def request_huggingface_async(en_problem: str) -> Optional[str]:
    return await asyncio.to_thread(request_huggingface, en_problem)
