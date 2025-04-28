import asyncio
import os

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import db_manager
from app.background.ping_model import start_ping_loop
from app.routers import health_check, users, problems, problem

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.getenv("DATABASE_URL")
    if not db_path:
        raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

    asyncio.create_task(start_ping_loop())

    await db_manager.init_connection(db_path)
    yield
    await db_manager.close_database_connection()


app = FastAPI(title="FastAPI", lifespan=lifespan)

web_client_url = os.getenv("WEB_CLIENT_URL")
if not web_client_url:
    raise RuntimeError("WEB_CLIENT_URL 환경변수가 설정되지 않았습니다.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[web_client_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(problem.router)
app.include_router(problems.router)
app.include_router(health_check.router)
