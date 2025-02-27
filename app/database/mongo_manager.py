import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern


class MongoManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, path: str):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_connection(path)
        return cls._instance

    async def _init_connection(self, path: str):
        async with self._lock:
            self.client = AsyncIOMotorClient(path)
            self.mongodb = self.client["SolPict"]
            print("데이터베이스 연결에 성공하였습니다.🙆‍♂️")

    async def close_database_connection(self):
        if self.client:
            self.client.close()
            print("데이터베이스 연결을 종료하였습니다.🙇‍♂️")

    async def __aenter__(self):
        self.session = await self.client.start_session()
        self.session.start_transaction(
            read_concern=ReadConcern("majority"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
        )
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            await self.session.abort_transaction()
            print("트랜잭션 롤백됨.")
        else:
            await self.session.commit_transaction()
            print("트랜잭션 커밋됨.")
        await self.session.end_session()
