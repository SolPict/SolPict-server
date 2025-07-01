import base64
from fastapi import APIRouter, File, Request, UploadFile, HTTPException
from app.dtos.users import ImageList
from app.external_services.math_ocr import request_ocr_from_upload_file
from app.dtos.problems import (
    MessageWithAnswer,
    OCRResponse,
    ReconstructInput,
    ReconstructResponse,
    SolveInput,
    SolveResponse,
    Submit,
    SubmitProblemInput,
    SubmitResponse,
    TranslateInput,
    TranslateResponse,
)

from app.services import problems as services
from app.database import db_manager
from app.external_services.huggingface import request_huggingface_async
from app.external_services.translation import request_translation
from app.utils.analyzeOcrText import analyze_ocr_text
from app.utils.divide_solving import divide_solving
from app.utils.get_answer import get_answer
from app.utils.get_answer_number import get_answer_number
from app.utils.reconstruct_solving import reconstruct_solving
from app.utils.upload_to_s3 import upload_to_s3
from app.utils.classify_problem_type import classify_problem_type
from app.utils.rate_limit import check_rate_limit
from app.utils.device_limit import check_device_request_limit

import json
import logging

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=ImageList)
async def get_problems_list(
    offset: int, problemLimit: int, problemType: str = "전체보기"
):
    images, next_offset = await services.get_problem_images(
        offset, problemLimit, problemType
    )
    return {"image_list": images, "offset": next_offset}


@router.post("/analyze/ocr", response_model=OCRResponse)
async def extract_ocr(file: UploadFile = File(...)):
    ocr_text = await request_ocr_from_upload_file(file)
    if not ocr_text:
        raise HTTPException(400, detail="OCR 실패")
    return {"ocr_text": ocr_text}


@router.post("/analyze/translate", response_model=TranslateResponse)
async def translate_problem(data: TranslateInput):
    lang = analyze_ocr_text(data.ocr_text)

    if lang == "Eng":
        return {"language": "Eng", "translated_text": data.ocr_text}

    if lang == "Kor":
        translated = request_translation([data.ocr_text], "EN")
        if not translated or not translated[0].get("text"):
            raise HTTPException(400, detail="번역 실패")
        return {"language": "Kor", "translated_text": translated[0]["text"]}

    raise HTTPException(400, detail="지원하지 않는 언어입니다.")


@router.post("/analyze/solve", response_model=SolveResponse)
async def solve_with_ai(request: Request, data: SolveInput):
    try:
        await check_rate_limit(request, api_name="solve", limit_time_sec=5)
    except HTTPException as error:
        logger.warning(f"요청 시간 제한: {error.status_code} - {error.detail}")
        raise error

    try:
        await check_device_request_limit(request, api_name="solve", max_calls=10)
    except HTTPException as error:
        logger.warning(f"디바이스 요청 횟수 제한: {error.status_code} - {error.detail}")
        raise error

    result = await request_huggingface_async(data.problem)

    if result == 503:
        raise HTTPException(503, detail="AI가 일시적으로 응답하지 않음")
    if result == 504:
        raise HTTPException(504, detail="AI 요청 타임아웃")
    if not result:
        raise HTTPException(400, detail="AI 풀이 실패")

    return {"ai_explanation": result}


@router.post("/analyze/reconstruct", response_model=ReconstructResponse)
async def reconstruct_solution(data: ReconstructInput):
    en_answer, math_answer = divide_solving(data.ai_explanation)
    translated = request_translation(en_answer, "KO")

    if not translated:
        raise HTTPException(400, detail="한글 번역 실패")

    ko_texts = [item["text"] for item in translated]
    ko_explanation = reconstruct_solving(ko_texts, math_answer)

    return {"ko_explanation": ko_explanation}


@router.post("/analyze/submit", response_model=SubmitResponse)
async def submit_problem(data: SubmitProblemInput):
    try:
        content = base64.b64decode(data.file_base64.split(",")[-1])
    except Exception:
        raise HTTPException(400, detail="파일 디코딩 실패")

    problem_type = classify_problem_type()
    key = await upload_to_s3(content, "sol.pic", data.filename, problem_type)

    if not key:
        raise HTTPException(500, detail="S3 업로드 실패")

    answer = get_answer_number(data.en_problem, get_answer(data.en_explanation))

    session = await db_manager.get_session()
    created = await services.create_problem(
        {
            "key": key,
            "problemType": problem_type,
            "solved_count": 1,
            "correct_count": 0,
            "ko_explanation": data.ko_explanation,
            "en_explanation": data.en_explanation,
            "answer": answer,
        },
        session=session,
    )

    if not created:
        raise HTTPException(500, detail="문제 저장 실패")

    return {"key": key, "message": "문제가 저장되었습니다."}


@router.post("/{problemId:path}/submissions", response_model=MessageWithAnswer)
async def count_up_answer_counting(user_submit: Submit, problemId: str):
    problem = await services.get_problem_by_key(problemId)
    if not problem:
        raise HTTPException(404, detail="문제를 찾을 수 없습니다.")

    is_correct = str(user_submit.user_answer) == str(problem.get("answer"))

    success = await services.record_submission(
        user_email=user_submit.email,
        problem_id=problem["_id"],
        is_correct=is_correct,
    )
    if not success:
        raise HTTPException(500, detail="채점 기록 실패")

    return {
        "message": "채점이 완료되었습니다.",
        "isAnswer": is_correct,
    }


@router.get("/{problemId:path}/explanation", response_model=str)
async def get_problem_explanation(problemId: str, language: str = "KO"):
    try:
        problem_key = "/".join(json.loads(problemId))
    except json.JSONDecodeError:
        raise HTTPException(400, detail="잘못된 problemId 형식입니다.")

    found_problem = await services.get_problem_by_key(problem_key)
    if not found_problem:
        raise HTTPException(404, detail="문제를 찾을 수 없습니다.")

    explanation = found_problem.get(
        "ko_explanation" if language.upper() == "KO" else "en_explanation"
    )

    if not explanation:
        raise HTTPException(404, detail="설명이 존재하지 않습니다.")

    return explanation
