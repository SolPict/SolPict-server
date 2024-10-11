from fastapi import APIRouter

from fastapi import Body
from fastapi.encoders import jsonable_encoder
from app.models.user import userSchema
from app.database import db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
async def create_user(user: userSchema = Body(...)):
    user = jsonable_encoder(user)
    Users = db.mongodb["users"]
    await Users.insert_one(user)
    return {"message": "정상적으로 잘 삽입되었습니다."}
