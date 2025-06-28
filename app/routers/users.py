from fastapi import APIRouter, HTTPException, Body, Query
from app.dtos.users import Email, ImageList, UserEmail, Message
from app.services import users as services
import json

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=Message)
async def create_user(user: UserEmail = Body(...)):
    success = await services.create_user(user)
    if not success:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    return {"message": "정상적으로 회원가입이 완료되었습니다."}


@router.delete("", response_model=Message)
async def delete_user(email: str = Query(...)):
    success = await services.delete_user_by_email(email)
    if not success:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {"message": "정상적으로 삭제되었습니다."}


@router.post("/reviewNote", response_model=ImageList)
async def get_problems_reviewNote_list(
    offset: int, problemLimit: int, user_email: Email
):
    images, next_offset = await services.get_review_note_images(
        user_email.email, offset, problemLimit
    )
    return {"image_list": images, "offset": next_offset}


@router.post("/reviewNote/{problemId}", response_model=Message)
async def add_problems_review_note(email: Email, problemId: str):
    problem_key = "/".join(json.loads(problemId))
    result = await services.add_review_note(email.email, problem_key)

    if result:
        return {"message": "리뷰노트에 잘 등록되었습니다."}
    else:
        return {"message": "리뷰노트에 등록하지 못하였습니다."}


@router.delete("/reviewNote/{problemId}", response_model=Message)
async def delete_review_problem(email: Email, problemId: str):
    problem_key = "/".join(json.loads(problemId))
    result = await services.delete_review_note(email.email, problem_key)

    if result:
        return {"message": "리뷰노트에서 잘 삭제되었습니다."}
    else:
        return {"message": "리뷰노트에서 삭제하지 못하였습니다."}
