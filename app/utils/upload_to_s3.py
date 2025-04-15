import os
import io

from aiobotocore.session import get_session
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_KEY")


async def upload_to_s3(
    file: io.BytesIO, bucket_name: str, file_name: str, problem_type: str
):
    try:
        bucket = bucket_name
        filename = file_name
        folder = "Sol_Pic/{}".format(problem_type)
        key = "{}/{}".format(folder, filename)

        session = get_session()
        async with session.create_client(
            "s3",
            region_name="ap-northeast-2",
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
        ) as client:

            file.seek(0)
            await client.put_object(Bucket=bucket, Key=key, Body=file)

            return key
    except ClientError as error:
        print("Failed to upload file: {}".format(error))
        return None
