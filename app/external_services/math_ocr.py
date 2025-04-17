import json
import os
from typing import Optional

import requests


def request_ocr(file_location: str) -> Optional[str]:
    try:
        with open(file_location, "rb") as file:
            response = requests.post(
                os.getenv("MATH_OCR_URL"),
                files={"file": file},
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
        ocr_result = json.loads(response.text).get("text", None)
        return ocr_result
    except Exception as error:
        print(f"OCR 요청에 실패했습니다. : {error}")
        return None
