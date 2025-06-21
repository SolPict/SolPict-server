from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal, Optional
from app.models.problem import problemSchema


class Email(BaseModel):
    email: str


class Owner(BaseModel):
    ID: str


class ImageData(BaseModel):
    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str
    Owner: Optional["Owner"] = None


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
