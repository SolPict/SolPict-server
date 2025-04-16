from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


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


class ImageList(BaseModel):
    image_list: List[ImageData]
    offset: Optional[int]
