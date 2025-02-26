from fastapi import APIRouter
import os
import json
import requests
import random
import shutil

from typing import List, Optional
from bson import json_util, ObjectId
from fastapi import Body, UploadFile, File
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from huggingface_hub import InferenceClient

from app.database import db
from app.models.problem import problemSchema
from app.utils.divide_solving import divide_solving
from app.utils.upload_to_s3 import upload_to_s3
from app.utils.get_answer import get_answer
from app.utils.get_answer_number import get_answer_number

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


class Analyze_Problem(BaseModel):
    _id: str
    key: str
    problemType: str
    solvingCount: int
    correctCount: int
    explanation: str
    answer: int | None


def request_ocr(file_location: str) -> Optional[str]:
    try:
        with open(file_location, "rb") as file:
            response = requests.post(
                os.getenv("MATH_OCR_URL"),
                files={"file": file},
                data={
                    "options_json": json.dumps(
                        {"math_inline_delimiters": ["$", "$"], "rm_spaces": True}
                    ),
                    "formats": ["text"],
                    "format_options": {"latex_styled": {"transforms": ["rm_newlines"]}},
                    "idiomatic_braces": True,
                },
                headers={
                    "app_id": os.getenv("MATH_OCR_ID"),
                    "app_key": os.getenv("MATH_OCR_KEY"),
                },
            )
        return json.loads(response.text).get("text", None)
    except Exception as error:
        print(f"OCR 요청 실패: {error}")
        return None


def request_translation(text: List[str], target_lang: str = "EN") -> Optional[str]:
    try:
        response = requests.post(
            os.getenv("TRANSLATE_URL"),
            json={"text": text, "target_lang": target_lang},
            headers={
                "Authorization": "DeepL-Auth-Key " + os.getenv("TRANSLATE_KEY"),
                "Content-Type": "application/json",
            },
        )
        return response.json().get("translations", [{}])
    except Exception as error:
        print(f"번역 요청 실패: {error}")
        return None


def request_huggingface(en_problem: str) -> Optional[str]:
    try:
        client = InferenceClient(api_key=os.getenv("HUGGING_FACE_API_KEY"))
        messages = [{"role": "user", "content": en_problem}]

        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-Math-1.5B-Instruct",
            messages=messages,
            max_tokens=500,
        )

        return completion.choices[0].message["content"]
    except Exception as error:
        print(f"Hugging Face 요청 실패: {error}")
        return None


async def create_problem(problem: problemSchema = Body(...)):
    problem = jsonable_encoder(problem)
    Problems = db.mongodb["problems"]
    new_problem = await Problems.insert_one(problem)
    created_problem = await Problems.find_one({"_id": new_problem.inserted_id})
    return created_problem


@router.post("/analyze", response_model=Analyze_Problem)
async def analyzeProblem(file: UploadFile = File(...)):
    try:
        file_location = f"images/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        kn_problem = request_ocr(file_location)
        if not kn_problem:
            return {"message": "OCR 분석 실패"}

        en_problem = request_translation([kn_problem], "EN")[0].get("text", None)
        if not en_problem:
            return {"message": "번역 실패"}

        en_answer = request_huggingface(en_problem)
        if not en_answer:
            return {"message": "AI 풀이 실패"}
        en_answer, math_answer = divide_solving(en_answer)

        ko_problem = request_translation(en_answer, "KO")
        ko_problem = [item["text"] for item in ko_problem]
        if not ko_problem:
            return {"message": "풀이 번역 실패"}

        result = ""
        for index in range(len(ko_problem)):
            try:
                result += ko_problem[index] + "$" + str(math_answer[index]) + "$"
            except IndexError:
                result += ko_problem[index]

        key = await upload_to_s3(file.file, "sol.pic", file.filename)
        if not key:
            return {"message": "이미지 업로드 실패"}

        created_problem = await create_problem(
            {
                "key": key,
                "problemType": random.choice(["대수학", "수와 연산", "기하학"]),
                "solvingCount": 1,
                "correctCount": 0,
                "explanation": result,
                "answer": get_answer_number(en_problem, get_answer(result)),
            }
        )
        if not created_problem:
            return {"message": "문제 저장 실패"}

        return created_problem

    except Exception as error:
        return {
            "message": "분석하는데 에러가 발생하였습니다.",
            "error": str(error),
        }, 500


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

    if updated_user:
        return {"message": "리뷰노트에 잘 등록되었습니다."}
    else:
        return {"error": "리뷰노트에 등록하지 못하였습니다."}
