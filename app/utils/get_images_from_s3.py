import os

from aiobotocore.session import get_session
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_KEY")


async def get_images_from_s3(bucket_name: str, problem_type: str = "전체보기"):
    try:
        folder_prefix = (
            "Sol_Pic" if problem_type == "전체보기" else f"Sol_Pic/{problem_type}"
        )

        session = get_session()
        async with session.create_client(
            "s3",
            region_name="ap-northeast-2",
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
        ) as client:
            paginator = client.get_paginator("list_objects_v2")
            all_images = []
            async for result in paginator.paginate(
                Bucket=bucket_name, Prefix=folder_prefix
            ):
                all_images.extend(result.get("Contents", []))

            return all_images

    except ClientError as error:
        print(f"이미지를 불러오는데 실패했습니다.: {error}")
        return None
