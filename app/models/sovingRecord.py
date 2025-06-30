from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class SolvingRecordSchema(BaseModel):
    _id: Optional[ObjectId]
    user_id: ObjectId = Field(...)
    problem_id: ObjectId = Field(...)
    solved_at: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "669668ddf4d1f9783752806a",
                "problem_id": "669dac2d0373baf913fcd064",
                "solved_at": "2025-06-30T10:00:00Z",
            }
        }


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
