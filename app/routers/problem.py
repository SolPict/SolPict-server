from fastapi import APIRouter
import os
import json
import requests
import random
import datetime
import shutil

from typing import List
from fastapi import Body, UploadFile, File, Header
from pydantic import BaseModel
from bson import json_util, ObjectId
from transformers import AutoModelForCausalLM, AutoTokenizer
from accelerate import Accelerator
from fastapi.encoders import jsonable_encoder

from app.database import db
from app.models.problem import problemSchema
from app.utils.divide_solving import divide_solving
from app.utils.upload_to_s3 import upload_to_s3

router = APIRouter(prefix="/problem", tags=["problem"])


class Email(BaseModel):
    email: str


class Problem_text(BaseModel):
    ocrText: str


class ProblemCollection(BaseModel):
    problems: List[problemSchema]


class Submit(BaseModel):
    email: str
    isUserAnswerCorrect: bool


@router.post("/analyze")
async def analyzeProblem(
    file: UploadFile = File(...),
    email: str = Header(None),
    uri: str = Header(None),
):

    try:

        file_location = f"images/{file.filename}"

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        OCR_response = requests.post(
            os.getenv("MATH_OCR_URL"),
            files={"file": open(file_location, "rb")},
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

        kn_problem = json.loads(OCR_response.text)["text"]

        translate_response = requests.post(
            os.getenv("TRANSLATE_URL"),
            json={"text": [kn_problem], "target_lang": "EN"},
            headers={
                "Authorization": "DeepL-Auth-Key " + os.getenv("TRANSLATE_KEY"),
                "Content-Type": "application/json",
            },
        )

        en_problem = translate_response.json()
        en_problem = en_problem["translations"][0]["text"]
        print(en_problem)
        accelerator = Accelerator()
        model_name = "Qwen/Qwen2.5-Math-1.5B-Instruct"
        device = "cuda"

        model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype="auto", device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        messages = [
            {
                "role": "system",
                "content": "Please solve this problem and number in boxed{}",
            },
            {"role": "user", "content": en_problem},
        ]
        model, tokenizer = accelerator.prepare(model, tokenizer)

        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(device)

        generated_ids = model.generate(**model_inputs, max_new_tokens=1024)
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        en_answer = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        en_answer, math_answer = divide_solving(en_answer)
        translate_answer = requests.post(
            os.getenv("TRANSLATE_URL"),
            json={"text": en_answer, "target_lang": "KO"},
            headers={
                "Authorization": "DeepL-Auth-Key " + os.getenv("TRANSLATE_KEY"),
                "Content-Type": "application/json",
            },
        )

        ko_problem = translate_answer.json()
        ko_problem = ko_problem["translations"]
        ko_problem = [item["text"] for item in ko_problem]

        result = ""

        for index in range(len(ko_problem)):
            try:
                result += ko_problem[index] + "$" + str(math_answer[index]) + "$"
            except IndexError:
                result += ko_problem[index]

        key = await upload_to_s3(file.file, "sol.pic", file.filename)

        if not key:
            return {"message": "이미지를 업로드하는데 문제가 발생하였습니다."}

        created_problem = await create_problem(
            {
                "key": key,
                "problemType": random.choice(["대수학", "수와 연산", "기하학"]),
                "solvingCount": 1,
                "correctCount": 0,
                "explanation": result,
                "answer": 2,
            }
        )

        if email:
            Users = db.mongodb["users"]
            now = datetime.datetime.now()
            new_history = (now.strftime("%Y-%m-%d"), created_problem["_id"])
            await Users.find_one_and_update(
                {"email": email}, {"$addToSet": {"history": new_history}}
            )
        return json_util.dumps(created_problem)

    except Exception as error:
        return {"message": "분석하는데 에러가 발생하였습니다.", "error": error}, 500


async def create_problem(problem: problemSchema = Body(...)):
    problem = jsonable_encoder(problem)
    Problems = db.mongodb["problems"]
    new_problem = await Problems.insert_one(problem)
    created_problem = await Problems.find_one({"_id": new_problem.inserted_id})
    return created_problem


@router.post("/solving/{problemId}")
async def count_up_answer_counting(user_submit: Submit, problemId: str):
    Problems = db.mongodb["problems"]
    update_fields = {"$addToSet": {"solving_user": user_submit.email}}

    if user_submit.isUserAnswerCorrect:
        update_fields["$addToSet"]["correct_users"] = user_submit.email

    await Problems.find_one_and_update(
        {"_id": ObjectId(problemId)}, update_fields, return_document=True
    )


@router.get("/{problemId}")
async def get_problem_image(problemId: str):
    problemId = "/".join(json.loads(problemId))
    Problems = db.mongodb["problems"]
    found_problem = await Problems.find_one({"key": problemId})

    return json_util.dumps(found_problem["explanation"])


@router.delete("/reviewNote/{problemId}")
async def delete_review_problem(email: Email, problemId: str):
    Users = db.mongodb["users"]
    delete_result = await Users.find_one_and_update(
        {"email": email.email},
        {"$pull": {"reviewNote": ObjectId(problemId)}},
    )

    if delete_result:
        return {"message": "리뷰노트에서 잘 삭제되었습니다."}, 200
    else:
        return {"error": "리뷰노트에서 삭제하지 못하였습니다."}, 500


@router.post("/reviewNote/{problemId}")
async def add_problems_reviewNote(email: Email, problemId: str):
    Users = db.mongodb["users"]
    updated_user = await Users.find_one_and_update(
        {"email": email.email},
        {"$addToSet": {"reviewNote": ObjectId(problemId)}},
    )

    if updated_user:
        return {"message": "리뷰노트에 잘 등록되었습니다."}, 200
    else:
        return {"error": "리뷰노트에 등록하지 못하였습니다."}, 500
