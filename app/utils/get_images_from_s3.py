import os

from aiobotocore.session import get_session
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_KEY")


async def get_images_from_s3(bucket_name: str, offset: int, problemLimit: int):
    try:
        session = get_session()
        async with session.create_client(
            "s3",
            region_name="ap-northeast-2",
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
        ) as client:
            paginator = client.get_paginator("list_objects")
            async for result in paginator.paginate(
                Bucket=bucket_name, Prefix="Sol_Pic"
            ):
                image_list = [image for image in result.get("Contents", [])]
                next_offset = offset + 1
                if offset * problemLimit + problemLimit >= len(image_list):
                    next_offset = None

                return {
                    "image_list": image_list[
                        offset * problemLimit : offset * problemLimit + problemLimit
                    ],
                    "offset": next_offset,
                }

    except ClientError as error:
        print("Failed to upload file: {}".format(error))
        return None
