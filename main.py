import os
import base64
import json
import requests

from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_db_client(app)
    yield
    await shutdown_db_client(app)


async def startup_db_client(app):
    try:
        app.mongodb_client = AsyncIOMotorClient(os.getenv("DATABASE_URL"))
        app.mongodb = app.mongodb_client.get_database("SolPict")
        print("데이터베이스 연결에 성공하였습니다.🙆‍♂️")
    except Exception as error:
        print("데이터베이스 연결에 실패하였습니다.🙅‍♂️", error)


async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("데이터베이스 연결을 성공적으로 종료하였습니다.🙇‍♂️")


app = FastAPI(lifespan=lifespan)

origins = [
    os.getenv("CLIENT_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Image(BaseModel):
    imageURI: str


@app.post("/problem/analyze")
async def analyzeProblem(image: Image):
    base64_data = image.imageURI.split(",")[1]
    image_data = base64.b64decode(base64_data)
    output_file_path = "temp_image.jpg"

    with open(output_file_path, "wb") as file:
        file.write(image_data)

    response = requests.post(
        os.getenv("MATH_OCR_URL"),
        files={"file": open("temp_image.jpg", "rb")},
        data={
            "options_json": json.dumps(
                {"math_inline_delimiters": ["$", "$"], "rm_spaces": True}
            ),
            "formats": ["text"],
            "format_options": {
                "latex_styled": {"transforms": ["rm_newlines", "rm_fonts"]}
            },
            "idiomatic_braces": True,
        },
        headers={
            "app_id": os.getenv("MATH_OCR_ID"),
            "app_key": os.getenv("MATH_OCR_KEY"),
        },
    )

    print(response)

    return {"message": "성공적으로 요청을 받았습니다."}
