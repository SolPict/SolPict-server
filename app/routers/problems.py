from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.utils.get_images_from_s3 import get_images_from_s3
from app.database import db_manager

router = APIRouter(prefix="/problems", tags=["problems"])


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


@router.get("", response_model=ImageList)
async def get_problems_list(
    offset: int, problemLimit: int, problemType: str = "전체보기"
):
    bucket_name = "sol.pic"
    image_list = await get_images_from_s3(bucket_name, problemType)

    if not image_list:
        return {"image_list": [], "offset": None}

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
    Users = db_manager.mongodb["users"]
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
