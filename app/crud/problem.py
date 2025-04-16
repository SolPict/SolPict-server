from pymongo.client_session import ClientSession
from fastapi.encoders import jsonable_encoder
from app.database import db_manager


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
