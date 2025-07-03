from ast import List
import datetime
from git import Optional
from pydantic import BaseModel


class Message(BaseModel):
    message: str


class UserEmail(BaseModel):
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


class ImageList(BaseModel):
    image_list: List[ImageData]
    offset: Optional[int]


class Email(BaseModel):
    email: str
