import os
from app.database.mongo_manager import MongoManager

db_manager = MongoManager(
    os.getenv("DATABASE_URL"),
)
