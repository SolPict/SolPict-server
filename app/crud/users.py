from fastapi.encoders import jsonable_encoder
from app.database import db_manager
from app.schemas.users import UserEmail
from app.utils import get_images_from_s3


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


async def add_review_note(email: str, problem_key: str):
    Users = db_manager.mongodb["users"]
    return await Users.find_one_and_update(
        {"email": email},
        {"$addToSet": {"reviewNote": problem_key}},
    )


async def delete_review_note(email: str, problem_key: str):
    Users = db_manager.mongodb["users"]
    return await Users.find_one_and_update(
        {"email": email},
        {"$pull": {"reviewNote": problem_key}},
    )


async def get_review_note_images(email: str, offset: int, limit: int):
    Users = db_manager.mongodb["users"]
    found_user = await Users.find_one({"email": email})

    if not found_user or "reviewNote" not in found_user:
        return [], None

    review_keys = found_user["reviewNote"]
    all_images = await get_images_from_s3("sol.pic")
    filtered_images = list(filter(lambda img: img["Key"] in review_keys, all_images))

    start = offset * limit
    end = start + limit
    next_offset = offset + 1 if end < len(filtered_images) else None

    return filtered_images[start:end], next_offset
