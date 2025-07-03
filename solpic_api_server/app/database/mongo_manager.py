import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


class MongoManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def init_connection(self, path: str):
        if hasattr(self, "client"):
            return

        async with self._lock:
            if not hasattr(self, "client"):
                self.client = AsyncIOMotorClient(path)
                self.mongodb = self.client["SolPict"]
                print("데이터베이스 연결 성공! 🙆‍♂️")

    async def close_database_connection(self):
        if hasattr(self, "client"):
            self.client.close()
            del self.client
            print("데이터베이스 연결 종료 🙇‍♂️")

    async def get_session(self):
        if not hasattr(self, "client"):
            raise RuntimeError("MongoDB 연결이 초기화되지 않았습니다.")

        return await self.client.start_session()
