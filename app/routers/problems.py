from fastapi import APIRouter
from pydantic import BaseModel
from bson import json_util

from app.utils.get_images_from_s3 import get_images_from_s3
from app.database import db

router = APIRouter(prefix="/problems", tags=["problems"])


class Email(BaseModel):
    email: str


@router.get("")
async def get_problems_list(offset: int, problemLimit: int):
    problems_image = await get_images_from_s3("sol.pic", offset, problemLimit)
    return json_util.dumps(problems_image)


@router.post("/history")
async def get_problems_history_list(user_email: Email):
    Users = db.mongodb["users"]
    Problems = db.mongodb["problems"]
    foundUser = await Users.find_one({"email": user_email.email})
    history_id_list = [problemId[1] for problemId in foundUser["history"]]
    history_list = await Problems.find({"_id": {"$in": history_id_list}}).to_list(100)

    history_list = [
        [foundUser["history"][index][0], history_list[index]]
        for index in range(len(history_list))
    ]

    return json_util.dumps(history_list)


@router.post("/reviewNote")
async def get_problems_reviewNote_list(user_email: Email):
    Users = db.mongodb["users"]
    foundUser = await Users.find_one({"email": user_email.email})
    review_id_list = foundUser["reviewNote"]
    problems_images = await get_images_from_s3("sol.pic")
    review_images = filter(
        lambda image: image["Key"] in review_id_list, problems_images
    )

    return json_util.dumps(review_images)
