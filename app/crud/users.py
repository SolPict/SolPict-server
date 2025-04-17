from fastapi.encoders import jsonable_encoder
from app.database import db_manager
from app.schemas.users import UserEmail


async def create_user(user: UserEmail) -> bool:
    Users = db_manager.mongodb["users"]
    user = jsonable_encoder(user)

    existing_user = await Users.find_one({"email": user["email"]})
    if existing_user:
        return False

    await Users.insert_one(user)
    return True


async def delete_user_by_email(email: str) -> bool:
    Users = db_manager.mongodb["users"]
    result = await Users.delete_one({"email": email})
    return result.deleted_count > 0
