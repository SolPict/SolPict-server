from typing import Optional, Literal
from pydantic import BaseModel, Field
from bson import ObjectId

StageStatus = Literal["pending", "in_progress", "success", "failed"]


class AnalyzeProgressSchema(BaseModel):
    _id: Optional[ObjectId]
    problem_id: ObjectId
    device_id: str = Field(...)
    ocr_stage: StageStatus = "pending"
    translate_to_en_stage: StageStatus = "pending"
    AI_inference_stage: StageStatus = "pending"
    translate_to_ko_stage: StageStatus = "pending"
    save_and_respond_stage: StageStatus = "pending"

    class Config:
        json_schema_extra = {
            "example": {
                "problem_id": "66db9c7f7ac2c2ed5ddc86c2",
                "device_id": "device-abc-123",
                "ocr_stage": "pending",
                "translate_to_en_stage": "pending",
                "AI_inference_stage": "pending",
                "translate_to_ko_stage": "pending",
                "save_and_respond_stage": "pending",
            }
        }


class UpdateAnalyzeProgressModel(BaseModel):
    ocr_stage: Optional[StageStatus]
    translate_to_en_stage: Optional[StageStatus]
    AI_inference_stage: Optional[StageStatus]
    translate_to_ko_stage: Optional[StageStatus]
    save_and_respond_stage: Optional[StageStatus]

    class Config:
        json_schema_extra = {
            "example": {"ocr_stage": "in_progress", "AI_inference_stage": "success"}
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
