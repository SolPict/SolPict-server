import os

from aiobotocore.session import get_session
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_KEY")


async def get_image_from_s3(bucket_name: str, key: str):
    try:
        session = get_session()
        async with session.create_client(
            "s3",
            region_name="ap-northeast-2",
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
        ) as client:

            s3_response = await client.get_object(
                Bucket=bucket_name,
                Key=key,
            )
            return await s3_response["Body"].read()
    except ClientError as error:
        print("파일 업로드에 실패 했습니다. : {}".format(error))
        return None
