from ast import List
from git import Optional
from pydantic import BaseModel

from app.schemas.problems import ImageData


class Message(BaseModel):
    message: str


class UserEmail(BaseModel):
    email: str


class ImageList(BaseModel):
    image_list: List[ImageData]
    offset: Optional[int]


class Email(BaseModel):
    email: str
