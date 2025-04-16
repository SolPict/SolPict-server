import asyncio
import os

from app.database import db_manager

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.background.ping_model import start_ping_loop
from app.routers import health_check, users
from app.routers import problems
from app.routers import problem

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.getenv("DATABASE_URL")
    asyncio.create_task(start_ping_loop())
    await db_manager.init_connection(db_path)
    yield
    await db_manager.close_database_connection()


app = FastAPI(title="FastAPI", lifespan=lifespan)

origins = [
    os.getenv("WEB_CLIENT_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(problem.router)
app.include_router(problems.router)
app.include_router(health_check.router)
