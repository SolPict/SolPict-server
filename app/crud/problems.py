from app.database import db_manager
from app.utils.get_images_from_s3 import get_images_from_s3


async def get_problem_images(offset: int, limit: int, problem_type: str = "전체보기"):
    bucket_name = "sol.pic"
    image_list = await get_images_from_s3(bucket_name, problem_type)

    if not image_list:
        return [], None

    start = offset * limit
    end = start + limit
    next_offset = offset + 1 if end < len(image_list) else None

    return image_list[start:end], next_offset


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
