import json
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas.problem import (
    Analyze_Problem,
    Email,
    Message,
    MessageWithAnswer,
    Submit,
)
from app.crud import problem as crud_problem
from app.database import db_manager
from app.external_services.huggingface import request_huggingface_async
from app.external_services.math_ocr import request_ocr
from app.external_services.translation import request_translation
from app.utils.analyzeOcrText import analyze_ocr_text
from app.utils.divide_solving import divide_solving
from app.utils.get_answer import get_answer
from app.utils.get_answer_number import get_answer_number
from app.utils.reconstruct_solving import reconstruct_solving
from app.utils.upload_to_s3 import upload_to_s3
from app.utils.classify_problem_type import classify_problem_type

router = APIRouter(prefix="/problem", tags=["problem"])


@router.post("/analyze", response_model=Analyze_Problem)
async def analyze_problem(file: UploadFile = File(...)):
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

        en_AI_answer = await request_huggingface_async(en_problem)
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
        created_problem = await crud_problem.create_problem(
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


@router.post("/{problemId:path}/solving", response_model=MessageWithAnswer)
async def count_up_answer_counting(user_submit: Submit, problemId: str):
    problem = await crud_problem.get_problem_by_key(problemId)
    if not problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    is_correct = str(user_submit.user_answer) == str(problem.get("answer"))
    await crud_problem.update_solving_info(
        problem["_id"], user_submit.email, is_correct
    )

    return {
        "message": "채점이 완료되었습니다.",
        "isAnswer": is_correct,
    }


@router.get("/{problemId:path}/explanation", response_model=str)
async def get_problem_explanation(problemId: str, language: str = "KO"):
    try:
        problem_key = "/".join(json.loads(problemId))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="잘못된 problemId 형식입니다.")

    found_problem = await crud_problem.get_problem_by_key(problem_key)
    if not found_problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")

    explanation = found_problem.get(
        "ko_explanation" if language.upper() == "KO" else "en_explanation"
    )

    if not explanation:
        raise HTTPException(status_code=404, detail="설명이 존재하지 않습니다.")

    return explanation


@router.post("/review-note/{problemId}", response_model=Message)
async def add_problems_review_note(email: Email, problemId: str):
    problem_key = "/".join(json.loads(problemId))
    result = await crud_problem.add_review_note(email.email, problem_key)

    if result:
        return {"message": "리뷰노트에 잘 등록되었습니다."}
    else:
        return {"error": "리뷰노트에 등록하지 못하였습니다."}


@router.delete("/review-note/{problemId}", response_model=Message)
async def delete_review_problem(email: Email, problemId: str):
    problem_key = "/".join(json.loads(problemId))
    result = await crud_problem.delete_review_note(email.email, problem_key)

    if result:
        return {"message": "리뷰노트에서 잘 삭제되었습니다."}
    else:
        return {"error": "리뷰노트에서 삭제하지 못하였습니다."}
