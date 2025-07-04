import requests
import json
import os
from io import BytesIO
from typing import Optional


async def request_ocr_from_upload_file(file) -> Optional[str]:
    try:
        file_bytes = await file.read()
        byte_stream = BytesIO(file_bytes)

        response = requests.post(
            os.getenv("MATH_OCR_URL"),
            files={"file": ("image.jpg", byte_stream, "image/jpeg")},
            data={
                "options_json": json.dumps(
                    {"math_inline_delimiters": ["$", "$"], "rm_spaces": True}
                ),
                "formats": ["text"],
                "format_options": {"latex_styled": {"transforms": ["rm_newlines"]}},
                "idiomatic_braces": True,
            },
            headers={
                "app_id": os.getenv("MATH_OCR_ID"),
                "app_key": os.getenv("MATH_OCR_KEY"),
            },
        )

        return response.json().get("text", None)

    except Exception as error:
        print(f"OCR 요청에 실패했습니다. : {error}")
        return None
