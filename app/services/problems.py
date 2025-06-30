from app.utils.get_images_from_s3 import get_images_from_s3
from pymongo.client_session import ClientSession
from fastapi.encoders import jsonable_encoder
from app.database import db_manager
from bson import ObjectId
from datetime import datetime, timezone


async def get_problem_images(offset: int, limit: int, problem_type: str = "전체보기"):
    bucket_name = "sol.pic"
    image_list = await get_images_from_s3(bucket_name, problem_type)

    if not image_list:
        return [], None

    start = offset * limit
    end = start + limit
    next_offset = offset + 1 if end < len(image_list) else None

    return image_list[start:end], next_offset


async def create_problem(problem: dict, session: ClientSession = None):
    problem = jsonable_encoder(problem)
    Problems = db_manager.mongodb["problems"]
    new_problem = await Problems.insert_one(problem, session=session)
    created_problem = await Problems.find_one(
        {"_id": new_problem.inserted_id}, session=session
    )

    return created_problem


async def get_problem_by_key(problem_key: str):
    Problems = db_manager.mongodb["problems"]
    return await Problems.find_one({"key": problem_key})


async def update_solving_info(problem_id, email: str, is_correct: bool):
    Users = db_manager.mongodb["users"]
    SolvingRecords = db_manager.mongodb["solving_records"]
    CorrectRecords = db_manager.mongodb["correct_records"]
    Problems = db_manager.mongodb["problems"]

    user = await Users.find_one({"email": email})

    if not user:
        return None

    user_id = user["_id"]

    await SolvingRecords.insert_one(
        {
            "user_id": user_id,
            "problem_id": ObjectId(problem_id),
            "solved_at": datetime.now(timezone.utc),
        }
    )

    if is_correct:
        await CorrectRecords.insert_one(
            {
                "user_id": user_id,
                "problem_id": ObjectId(problem_id),
                "answered_at": datetime.now(timezone.utc),
            }
        )

    await Problems.update_one(
        {"_id": ObjectId(problem_id)},
        {"$inc": {"solved_count": 1, "correct_count": 1 if is_correct else 0}},
    )

    return True


async def record_submission(
    user_email: str, problem_id: ObjectId, is_correct: bool
) -> bool:
    Users = db_manager.mongodb["users"]
    Problems = db_manager.mongodb["problems"]
    SolvingRecords = db_manager.mongodb["solving_records"]
    CorrectRecords = db_manager.mongodb["correct_records"]

    user = await Users.find_one({"email": user_email})
    if not user:
        return False

    await SolvingRecords.insert_one(
        {
            "user_id": user["_id"],
            "problem_id": problem_id,
            "solved_at": datetime.now(timezone.utc),
        }
    )

    if is_correct:
        await CorrectRecords.insert_one(
            {
                "user_id": user["_id"],
                "problem_id": problem_id,
                "answered_at": datetime.now(timezone.utc),
            }
        )

    await Problems.update_one(
        {"_id": problem_id},
        {"$inc": {"solved_count": 1, "correct_count": 1 if is_correct else 0}},
    )

    return True
