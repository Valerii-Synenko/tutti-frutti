from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[settings.mongo_db_name]


def get_fruits_collection():
    return get_database()["fruits"]


def get_comments_collection():
    return get_database()["comments"]


async def ensure_indexes() -> None:
    fruits = get_fruits_collection()
    await fruits.create_index(
        [("name", "text"), ("description", "text"), ("origin", "text"), ("tags", "text")]
    )
    await fruits.create_index("slug", unique=True)

    comments = get_comments_collection()
    await comments.create_index("fruit_slug")
