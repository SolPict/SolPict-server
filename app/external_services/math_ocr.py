import json
import os
from io import BytesIO
from typing import Optional

import requests
from PIL import Image


def pil_to_bytesio(pil_image: Image.Image, format: str = "JPEG") -> BytesIO:
    byte_io = BytesIO()
    pil_image.save(byte_io, format=format)
    byte_io.seek(0)
    return byte_io


def request_ocr(pil_image: Image.Image) -> Optional[str]:
    try:
        image_bytes = pil_to_bytesio(pil_image)

        response = requests.post(
            os.getenv("MATH_OCR_URL"),
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
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
