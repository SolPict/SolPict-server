from typing import Optional
from pydantic import BaseModel, Field


class problemSchema(BaseModel):
    uri: str = Field(...)
    problemType: str = Field(...)
    solvingCount: int = Field(..., ge=0)
    correctCount: int = Field(..., ge=0)
    explanation: str = Field(...)
    answer: int = Field(..., gt=0, le=4)

    class Config:
        schema_extra = {
            "example": {
                "uri": "dataUri",
                "problemType": "대수학",
                "solvingCount": 335,
                "correctCount": 220,
                "explanation": "문제를 해결하려면 이차 방정식~~",
                "answer": 2,
            }
        }


class IncrementCountModel(BaseModel):
    solvingCount: Optional[int] = Field(..., ge=0)
    correctCount: Optional[int] = Field(..., ge=0)

    class Config:
        schema_extra = {"example": {"solvingCount": 336, "correctCount": 221}}


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
