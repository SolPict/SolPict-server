from fastapi import APIRouter

from fastapi import Body
from fastapi.encoders import jsonable_encoder
from app.models.user import userSchema
from app.database import db_manager
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class Message(BaseModel):
    message: str


@router.post("", response_model=Message)
async def create_user(user: userSchema = Body(...)):
    user = jsonable_encoder(user)
    Users = db_manager.mongodb["users"]
    await Users.insert_one(user)
    return {"message": "정상적으로 잘 삽입되었습니다."}
