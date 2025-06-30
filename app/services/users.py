from fastapi.encoders import jsonable_encoder
from app.database import db_manager
from app.dtos.users import UserEmail
from app.utils import get_images_from_s3
from bson import ObjectId


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
    ReviewNotes = db_manager.mongodb["review_notes"]

    user = await Users.find_one({"email": email})
    if not user:
        return False

    existing = await ReviewNotes.find_one(
        {"user_id": user["_id"], "problem_id": ObjectId(problem_key)}
    )

    if existing:
        return False

    await ReviewNotes.insert_one(
        {"user_id": user["_id"], "problem_id": ObjectId(problem_key)}
    )

    return True


async def delete_review_note(email: str, problem_key: str):
    Users = db_manager.mongodb["users"]
    ReviewNotes = db_manager.mongodb["review_notes"]

    user = await Users.find_one({"email": email})
    if not user:
        return False

    result = await ReviewNotes.delete_one(
        {"user_id": user["_id"], "problem_id": ObjectId(problem_key)}
    )

    return result.deleted_count > 0


async def get_review_note_images(email: str, offset: int, limit: int):
    Users = db_manager.mongodb["users"]
    ReviewNotes = db_manager.mongodb["review_notes"]

    user = await Users.find_one({"email": email})

    if not user:
        return [], None

    cursor = ReviewNotes.find({"user_id": user["_id"]})
    review_docs = await cursor.to_list(length=None)
    problem_keys = [str(doc["problem_id"]) for doc in review_docs]

    all_images = await get_images_from_s3("sol.pic")
    filtered_images = list(filter(lambda img: img["Key"] in problem_keys, all_images))

    start = offset * limit
    end = start + limit
    next_offset = offset + 1 if end < len(filtered_images) else None

    return filtered_images[start:end], next_offset
