from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


class UserSchema(BaseModel):
    _id: Optional[ObjectId]
    email: EmailStr = Field(...)

    class Config:
        json_schema_extra = {"example": {"email": "hoho123@gmail.com"}}


class UpdateUserModel(BaseModel):
    email: EmailStr

    class Config:
        json_schema_extra = {"example": {"email": "example@test.com"}}


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}
