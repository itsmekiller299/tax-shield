from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    return db.db


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]
    await create_indexes()


async def close_mongo_connection():
    if db.client:
        db.client.close()


async def create_indexes():
    database = db.db
    await database.users.create_index("email", unique=True)
    await database.transactions.create_index([("user_id", 1), ("date", -1)])
    await database.documents.create_index([("user_id", 1), ("financial_year", 1)])
    await database.obligations.create_index([("user_id", 1), ("status", 1)])
    await database.deadlines.create_index([("user_id", 1), ("due_date", 1)])
    await database.scenarios.create_index([("user_id", 1), ("created_at", -1)])
    await database.tax_payments.create_index([("user_id", 1), ("payment_date", -1)])
    await database.ais_records.create_index([("user_id", 1), ("financial_year", 1)])
    await database.form26as_records.create_index([("user_id", 1), ("financial_year", 1)])
    await database.chat_messages.create_index([("user_id", 1), ("created_at", -1)])