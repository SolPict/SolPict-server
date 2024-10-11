from typing import List, Tuple, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class userSchema(BaseModel):
    email: EmailStr = Field(...)
    history: List[Tuple[datetime, str]] = Field(...)
    reviewNote: List[str] = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "hoho123@gamil.com",
                "history": [
                    ("2024-09-20", "669668ddf4d1f9783752806a"),
                    ("2024-09-22", "669dac2d0373baf913fcd064"),
                ],
                "reviewNote": ["669668ddf4d1f9783752806a", "669dac2d0373baf913fcd064"],
            }
        }


class UpdateUserModel(BaseModel):
    reviewNote: Optional[List[str]]

    class Config:
        json_schema_extra = {
            "example": {
                "reviewNote": ["669668ddf4d1f9783752806a"],
            }
        }


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
