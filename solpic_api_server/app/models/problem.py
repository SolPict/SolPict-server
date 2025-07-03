from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class ProblemSchema(BaseModel):
    _id: Optional[ObjectId]
    key: str = Field(...)
    ocr: str = Field(...)
    problemType: str = Field(...)
    ko_explanation: str = Field(...)
    en_explanation: str = Field(...)
    answer: int = Field(..., gt=0, le=4)

    class Config:
        json_schema_extra = {
            "example": {
                "key": "dataUri",
                "ocr": "연립방정식 $\\left...",
                "problemType": "대수학",
                "ko_explanation": "문제를 해결하려면...",
                "en_explanation": "To solve the problem...",
                "answer": 2,
            }
        }


class IncrementCountModel(BaseModel):
    solved_count: Optional[int] = Field(default=0, ge=0)
    correct_count: Optional[int] = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {"example": {"solved_count": 152, "correct_count": 97}}


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {
        "error": error,
        "code": code,
        "message": message,
    }
