import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
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


@app.get("/")
async def root():
    return {"message": "Hello World"}
