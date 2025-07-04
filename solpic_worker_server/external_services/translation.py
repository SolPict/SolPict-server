from typing import List, Optional

import os
import requests


def request_translation(text: List[str], target_lang: str = "EN") -> Optional[str]:
    try:
        response = requests.post(
            os.getenv("TRANSLATE_URL"),
            json={"text": text, "target_lang": target_lang},
            headers={
                "Authorization": "DeepL-Auth-Key " + os.getenv("TRANSLATE_KEY"),
                "Content-Type": "application/json",
            },
        )
        return response.json().get("translations", [{}])
    except Exception as error:
        print(f"번역 요청 실패 했습니다. : {error}")
        return None
