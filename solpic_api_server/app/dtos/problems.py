from pydantic import BaseModel
from typing import Literal, Optional


class Submit(BaseModel):
    email: str
    user_answer: Optional[Literal["1", "2", "3", "4", "5"]]


class MessageWithAnswer(BaseModel):
    message: str
    isAnswer: bool


class TranslateInput(BaseModel):
    ocr_text: str


class SolveInput(BaseModel):
    problem: str


class ReconstructInput(BaseModel):
    ai_explanation: str


class SubmitProblemInput(BaseModel):
    file_base64: str
    filename: str
    en_explanation: str
    ko_explanation: str
    en_problem: str


class OCRResponse(BaseModel):
    ocr_text: str


class TranslateResponse(BaseModel):
    language: Literal["Kor", "Eng"]
    translated_text: str


class SolveResponse(BaseModel):
    ai_explanation: str


class ReconstructResponse(BaseModel):
    ko_explanation: str


class SubmitResponse(BaseModel):
    key: str
    message: str
