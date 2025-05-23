from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class problemSchema(BaseModel):
    _id: Optional[ObjectId]
    key: str = Field(...)
    ocr: str = Field(...)
    problemType: str = Field(...)
    solving_users: List[str] = Field(...)
    correct_users: List[str] = Field(...)
    ko_explanation: str = Field(...)
    en_explanation: str = Field(...)
    answer: int = Field(..., gt=0, le=4)

    class Config:
        json_schema_extra = {
            "example": {
                "key": "dataUri",
                "ocr": "2. 연립방정식 $\\left\\{\\begin{array}{l}8 x+5 y=4 \\ 3 x-a ~~~",
                "problemType": "대수학",
                "solving_users": [
                    "hoho@naver.com",
                    "hoho123@naver.com",
                    "hoho1212@naver.com",
                    ...,
                ],
                "correct_users": ["hoho@naver.com", "hoho123@naver.com", ...],
                "ko_explanation": "문제를 해결하려면 이차 방정식~~",
                "en_explanation": "This problem is ~~",
                "answer": 2,
            }
        }


class IncrementCountModel(BaseModel):
    solving_users: Optional[int] = Field(..., ge=0)
    correct_users: Optional[int] = Field(..., ge=0)

    class Config:
        json_schema_extra = {"example": {"solving_users": 336, "correct_users": 221}}


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
