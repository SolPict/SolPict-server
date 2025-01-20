from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, TypedDict, Union
from datetime import datetime

from app.utils.get_images_from_s3 import get_images_from_s3
from app.database import db

router = APIRouter(prefix="/problems", tags=["problems"])


class Email(BaseModel):
    email: str


class Owner(TypedDict):
    ID: str


class ImageData(TypedDict):
    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str
    Owner: Owner


class ImageList(TypedDict):
    image_list: List[ImageData]
    offset: Union[int, None]


@router.get("", response_model=ImageList)
async def get_problems_list(offset: int, problemLimit: int):
    image_list = await get_images_from_s3("sol.pic")
    next_offset = offset + 1
    if offset * problemLimit + problemLimit >= len(image_list):
        next_offset = None

    return {
        "image_list": image_list[
            offset * problemLimit : offset * problemLimit + problemLimit
        ],
        "offset": next_offset,
    }


@router.post("/reviewNote", response_model=ImageList)
async def get_problems_reviewNote_list(
    offset: int, problemLimit: int, user_email: Email
):
    Users = db.mongodb["users"]
    foundUser = await Users.find_one({"email": user_email.email})
    review_id_list = foundUser["reviewNote"]
    problems_images = await get_images_from_s3("sol.pic")
    problems_images = list(
        filter(lambda image: image["Key"] in review_id_list, problems_images)
    )
    next_offset = offset + 1
    if offset * problemLimit + problemLimit >= len(problems_images):
        next_offset = None

    return {
        "image_list": problems_images[
            offset * problemLimit : offset * problemLimit + problemLimit
        ],
        "offset": next_offset,
    }
