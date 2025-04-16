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
        print(f"Hugging Face 요청에 실패했습니다. : {error}")
        return None


async def request_huggingface_async(en_problem: str) -> Optional[str]:
    return await asyncio.to_thread(request_huggingface, en_problem)
