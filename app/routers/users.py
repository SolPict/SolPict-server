from fastapi import APIRouter, HTTPException, Body
from app.schemas.users import UserCreate, UserEmail, Message
from app.crud import users as crud_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=Message)
async def create_user(user: UserCreate = Body(...)):
    success = await crud_user.create_user(user)
    if not success:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    return {"message": "정상적으로 회원가입이 완료되었습니다."}


@router.delete("", response_model=Message)
async def delete_user(user: UserEmail = Body(...)):
    success = await crud_user.delete_user_by_email(user.email)
    if not success:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {"message": "정상적으로 삭제되었습니다."}
