from pydantic import BaseModel


class Message(BaseModel):
    message: str


class UserEmail(BaseModel):
    email: str


class UserCreate(BaseModel):
    email: str
    password: str
