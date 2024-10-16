import os

from app.database import db

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import users
from app.routers import problems
from app.routers import problem

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect_to_database(os.getenv("DATABASE_URL"))
    yield
    await db.close_database_connection()


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
