import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern


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

    async def __aenter__(self):
        if not hasattr(self, "client"):
            raise RuntimeError(
                "MongoDB 연결이 초기화되지 않았습니다. 먼저 init_connection()을 호출하세요."
            )

        self.session = await self.client.start_session()
        self.session.start_transaction(
            read_concern=ReadConcern("majority"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
        )
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if hasattr(self, "session"):
            if exc_type is not None:
                await self.session.abort_transaction()
            else:
                await self.session.commit_transaction()
            await self.session.end_session()
            del self.session
