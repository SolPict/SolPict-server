from fastapi import APIRouter
import json

from typing import List
from pydantic import BaseModel
from bson import json_util, ObjectId

from app.database import db
from app.models.problem import problemSchema

router = APIRouter(prefix="/problem", tags=["problem"])


class Email(BaseModel):
    email: str


class Problem_text(BaseModel):
    ocrText: str


class Problem_collection(BaseModel):
    problems: List[problemSchema]


class Submit(BaseModel):
    email: str
    isUserAnswerCorrect: bool


class Message(BaseModel):
    message: str


@router.post("/solving/{problemId}", response_model=Message)
async def count_up_answer_counting(user_submit: Submit, problemId: str):
    Problems = db.mongodb["problems"]
    update_fields = {"$addToSet": {"solving_user": user_submit.email}}

    if user_submit.isUserAnswerCorrect:
        update_fields["$addToSet"]["correct_users"] = user_submit.email

    await Problems.find_one_and_update(
        {"_id": ObjectId(problemId)}, update_fields, return_document=True
    )

    return {"message": "올바르게 업데이트가 완료되었습니다."}


@router.get("/{problemId}", response_model=str)
async def get_problem_image(problemId: str):
    problemId = "/".join(json.loads(problemId))
    Problems = db.mongodb["problems"]
    found_problem = await Problems.find_one({"key": problemId})

    return json_util.dumps(found_problem["explanation"])


@router.delete("/reviewNote/{problemId}", response_model=Message)
async def delete_review_problem(email: Email, problemId: str):
    problemId = "/".join(json.loads(problemId))
    Users = db.mongodb["users"]
    delete_result = await Users.find_one_and_update(
        {"email": email.email},
        {"$pull": {"reviewNote": problemId}},
    )

    if delete_result:
        return {"message": "리뷰노트에서 잘 삭제되었습니다."}
    else:
        return {"error": "리뷰노트에서 삭제하지 못하였습니다."}


@router.post("/reviewNote/{problemId}", response_model=Message)
async def add_problems_reviewNote(email: Email, problemId: str):
    Users = db.mongodb["users"]
    updated_user = await Users.find_one_and_update(
        {"email": email.email},
        {"$addToSet": {"reviewNote": "/".join(json.loads(problemId))}},
    )
    print(updated_user)
    if updated_user:
        return {"message": "리뷰노트에 잘 등록되었습니다."}
    else:
        return {"error": "리뷰노트에 등록하지 못하였습니다."}
