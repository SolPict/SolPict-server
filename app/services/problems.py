from app.utils.get_images_from_s3 import get_images_from_s3
from pymongo.client_session import ClientSession
from fastapi.encoders import jsonable_encoder
from app.database import db_manager


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
    Problems = db_manager.mongodb["problems"]
    update_fields = {"$addToSet": {"solving_users": email}}

    if is_correct:
        update_fields["$addToSet"]["correct_users"] = email

    return await Problems.find_one_and_update({"_id": problem_id}, update_fields)
