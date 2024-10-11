from pymongo import MongoClient
from pymongo.database import Database
from motor.motor_asyncio import AsyncIOMotorClient


class MongoManager:
    client: MongoClient = None
    mongodb: Database = None

    async def connect_to_database(self, path: str):
        try:
            self.client = AsyncIOMotorClient(path)
            self.mongodb = self.client.get_database("SolPict")
            print("데이터베이스 연결에 성공하였습니다.🙆‍♂️")
        except Exception as error:
            print(f"데이터베이스 연결에 실패하였습니다.🙅‍♂️: {error}")

    async def close_database_connection(self):
        if self.client:
            self.client.close()
            print("데이터베이스 연결을 성공적으로 종료하였습니다.🙇‍♂️")
