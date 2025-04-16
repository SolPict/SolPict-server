from fastapi import APIRouter
from app.schemas.problems import Email, ImageList
from app.crud import problems as crud_problems

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("", response_model=ImageList)
async def get_problems_list(
    offset: int, problemLimit: int, problemType: str = "전체보기"
):
    images, next_offset = await crud_problems.get_problem_images(
        offset, problemLimit, problemType
    )
    return {"image_list": images, "offset": next_offset}


@router.post("/reviewNote", response_model=ImageList)
async def get_problems_reviewNote_list(
    offset: int, problemLimit: int, user_email: Email
):
    images, next_offset = await crud_problems.get_review_note_images(
        user_email.email, offset, problemLimit
    )
    return {"image_list": images, "offset": next_offset}
