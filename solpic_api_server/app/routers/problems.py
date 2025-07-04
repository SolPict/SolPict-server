from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException
from app.dtos.users import ImageList
from app.dtos.problems import (
    MessageWithAnswer,
    Submit,
)

from app.services import problems as services
from app.database import db_manager
from celery_client import celery_app

import base64
import json
import logging

from solpic_api_server.app.utils.device_limit import check_device_request_limit
from solpic_api_server.app.utils.rate_limit import check_rate_limit

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


@router.post("/analyze/start")
async def start_analysis(
    request: Request, device_id: str = Form(...), file: UploadFile = File(...)
):
    try:
        await check_rate_limit(request, api_name="analyze", limit_time_sec=5)
        await check_device_request_limit(request, api_name="analyze", max_calls=10)

        session = await db_manager.get_session()
        problem_id = await services.create_problem(session)
        await services.create_analyze_progress(session, problem_id, device_id)

        content = await file.read()
        file_base64 = base64.b64encode(content).decode("utf-8")
        celery_app.send_task(
            "tasks.analyze_pipeline.run_full_analysis",
            args=[problem_id, device_id, file_base64, file.filename],
        )

        return {"problem_id": problem_id, "device_id": device_id}

    except HTTPException as error:
        logger.warning(f"문제 분석에러 {error.status_code}: {error.detail}")
        raise error
    except Exception as error:
        logger.error(f"문제 분석에러 {str(error)}")
        raise HTTPException(status_code=500, detail="분석 요청 실패")


@router.get("/analyze/progress")
async def get_analyze_progress(device_id: str):
    progress = await services.get_analyze_progress_by_device(device_id)

    if not progress:
        raise HTTPException(
            status_code=404, detail="분석 진행 상태를 찾을 수 없습니다."
        )

    progress["_id"] = str(progress["_id"])
    progress["problem_id"] = str(progress["problem_id"])

    return progress


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
