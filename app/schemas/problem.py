from typing import List, Literal, Optional
from pydantic import BaseModel

from app.models.problem import problemSchema


class Email(BaseModel):
    email: str


class Problem_text(BaseModel):
    ocrText: str


class Problem_collection(BaseModel):
    problems: List[problemSchema]


class Submit(BaseModel):
    email: str
    user_answer: Optional[Literal["1", "2", "3", "4", "5"]]


class Message(BaseModel):
    message: str


class Analyze_Problem(BaseModel):
    _id: str
    key: str
    problemType: str
    solvingCount: int
    correctCount: int
    answer: int | None
    ko_explanation: str
    en_explanation: str


class MessageWithAnswer(BaseModel):
    message: str
    isAnswer: bool
