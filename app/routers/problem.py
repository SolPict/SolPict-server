from fastapi import APIRouter, HTTPException
from pymongo.client_session import ClientSession
import os
import json
import requests
import shutil

from typing import List, Literal, Optional
from fastapi import UploadFile, File
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from huggingface_hub import InferenceClient

from app.database import db_manager
from app.models.problem import problemSchema
from app.utils.analyzeOcrText import analyze_ocr_text
from app.utils.divide_solving import divide_solving
from app.utils.reconstruct_solving import reconstruct_solving
from app.utils.upload_to_s3 import upload_to_s3
from app.utils.get_answer import get_answer
from app.utils.get_answer_number import get_answer_number
from app.utils.classify_problem_type import classify_problem_type

router = APIRouter(prefix="/problem", tags=["problem"])


class Email(BaseModel):
    email: str


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
        ocr_result = json.loads(response.text).get("text", None)
        return ocr_result
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


async def create_problem(problem: dict, session: ClientSession = None):
    problem = jsonable_encoder(problem)
    Problems = db_manager.mongodb["problems"]
    new_problem = await Problems.insert_one(problem, session=session)
    created_problem = await Problems.find_one(
        {"_id": new_problem.inserted_id}, session=session
    )

    return created_problem


@router.post("/analyze", response_model=Analyze_Problem)
async def analyzeProblem(file: UploadFile = File(...)):
    try:
        file_location = f"images/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ocr_result = request_ocr(file_location)
        if not ocr_result:
            raise HTTPException(status_code=400, detail="OCR 분석 실패")

        try:
            lang = analyze_ocr_text(ocr_result)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))

        if lang == "Eng":
            en_problem = ocr_result
        elif lang == "Kor":
            translated = request_translation([ocr_result], "EN")
            en_problem = translated[0].get("text") if translated else None
            if not en_problem:
                raise HTTPException(status_code=400, detail="번역 실패")
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 언어입니다.")

        en_AI_answer = request_huggingface(en_problem)
        if not en_AI_answer:
            raise HTTPException(status_code=400, detail="AI 풀이 실패")

        en_answer, math_answer = divide_solving(en_AI_answer)
        ko_answer = request_translation(en_answer, "KO")
        ko_answer = [item["text"] for item in ko_answer] if ko_answer else None
        if not ko_answer:
            raise HTTPException(status_code=400, detail="풀이 번역 실패")

        ko_explanation = reconstruct_solving(ko_answer, math_answer)
        en_explanation = en_AI_answer

        problem_type = classify_problem_type()
        key = await upload_to_s3(file.file, "sol.pic", file.filename, problem_type)
        if not key:
            raise HTTPException(status_code=500, detail="이미지 업로드 실패")

        session = await db_manager.get_session()
        created_problem = await create_problem(
            {
                "key": key,
                "problemType": problem_type,
                "solvingCount": 1,
                "correctCount": 0,
                "ko_explanation": ko_explanation,
                "en_explanation": en_explanation,
                "answer": get_answer_number(en_problem, get_answer(en_AI_answer)),
            },
            session=session,
        )

        if not created_problem:
            raise HTTPException(status_code=500, detail="문제 저장 실패")

        return created_problem

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(error)}")


@router.post("/solving/{problemId:path}", response_model=MessageWithAnswer)
async def count_up_answer_counting(user_submit: Submit, problemId: str):
    Problems = db_manager.mongodb["problems"]
    problem = await Problems.find_one({"key": problemId})

    if not problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    correct_answer = problem.get("answer")
    update_fields = {"$addToSet": {"solving_users": user_submit.email}}

    if user_submit.user_answer == correct_answer:
        update_fields["$addToSet"]["correct_users"] = user_submit.email

    await Problems.find_one_and_update(
        {"_id": problem["_id"]},
        update_fields,
    )

    return {
        "message": "채점이 완료되었습니다.",
        "isAnswer": str(correct_answer) == str(user_submit.user_answer),
    }


@router.get("/{problemId:path}", response_model=str)
async def get_problem_explanation(problemId: str, language: str = "KO"):
    try:
        problem_key = "/".join(json.loads(problemId))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="잘못된 problemId 형식입니다.")

    Problems = db_manager.mongodb["problems"]
    found_problem = await Problems.find_one({"key": problem_key})

    if not found_problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    if language.upper() == "KO":
        explanation = found_problem.get("ko_explanation")
    elif language.upper() == "EN":
        explanation = found_problem.get("en_explanation")
    else:
        raise HTTPException(
            status_code=400, detail="지원하지 않는 언어입니다. (KO or EN)"
        )

    if not explanation:
        raise HTTPException(status_code=404, detail="설명이 존재하지 않습니다.")

    return explanation


@router.delete("/reviewNote/{problemId}", response_model=Message)
async def delete_review_problem(email: Email, problemId: str):
    problemId = "/".join(json.loads(problemId))
    Users = db_manager.mongodb["users"]
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
    Users = db_manager.mongodb["users"]
    updated_user = await Users.find_one_and_update(
        {"email": email.email},
        {"$addToSet": {"reviewNote": "/".join(json.loads(problemId))}},
    )

    if updated_user:
        return {"message": "리뷰노트에 잘 등록되었습니다."}
    else:
        return {"error": "리뷰노트에 등록하지 못하였습니다."}
