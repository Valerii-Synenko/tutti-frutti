import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, Query, status

from app.auth import require_auth
from app.database import ensure_indexes, get_comments_collection, get_fruits_collection
from app.schemas import CommentIn, CommentOut, FruitCreate, FruitOut, FruitUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    from app.seed import main as seed
    await seed()
    yield


app = FastAPI(
    title="Tutti Frutti — Catalogue Service",
    description="Fruit catalogue backed by MongoDB, chosen because fruits have "
    "genuinely irregular, fruit-specific attribute sets (ripening climate, "
    "shelf life, allergen notes, etc).",
    version="1.0.0",
    lifespan=lifespan,
)


def _to_object_id(fruit_id: str) -> ObjectId:
    try:
        return ObjectId(fruit_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid fruit id")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "catalogue-service"}


@app.get("/fruits", response_model=list[FruitOut], tags=["fruits"])
async def list_fruits(
    q: str | None = Query(default=None, description="Free-text search across name/description/origin/tags"),
    tag: str | None = Query(default=None),
    organic_only: bool = Query(default=False),
    in_season_month: int | None = Query(default=None, ge=1, le=12),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    collection = get_fruits_collection()
    filter_query: dict = {}

    if q:
        # Case-insensitive substring match (partial), so "app" matches "Apple".
        # re.escape guards against regex-special chars in user input.
        pattern = {"$regex": re.escape(q), "$options": "i"}
        filter_query["$or"] = [
            {"name": pattern},
            {"description": pattern},
            {"origin": pattern},
            {"tags": pattern},
        ]
    if tag:
        filter_query["tags"] = tag
    if organic_only:
        filter_query["is_organic"] = True
    if in_season_month:
        filter_query["seasonal_months"] = in_season_month

    cursor = collection.find(filter_query).skip(offset).limit(limit)
    return [doc async for doc in cursor]


@app.get("/fruits/{slug}", response_model=FruitOut, tags=["fruits"])
async def get_fruit(slug: str):
    collection = get_fruits_collection()
    doc = await collection.find_one({"slug": slug})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fruit not found")
    return doc


@app.post("/fruits", response_model=FruitOut, status_code=status.HTTP_201_CREATED, tags=["fruits"])
async def create_fruit(payload: FruitCreate, _user_id: str = Depends(require_auth)):
    collection = get_fruits_collection()
    existing = await collection.find_one({"slug": payload.slug})
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    result = await collection.insert_one(payload.model_dump())
    doc = await collection.find_one({"_id": result.inserted_id})
    return doc


@app.patch("/fruits/{fruit_id}", response_model=FruitOut, tags=["fruits"])
async def update_fruit(fruit_id: str, payload: FruitUpdate, _user_id: str = Depends(require_auth)):
    collection = get_fruits_collection()
    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await collection.find_one_and_update(
        {"_id": _to_object_id(fruit_id)}, {"$set": update_data}, return_document=True
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fruit not found")
    return result


@app.delete("/fruits/{fruit_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["fruits"])
async def delete_fruit(fruit_id: str, _user_id: str = Depends(require_auth)):
    collection = get_fruits_collection()
    result = await collection.delete_one({"_id": _to_object_id(fruit_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fruit not found")


# ---- Comments ---------------------------------------------------------------

@app.get("/fruits/{slug}/comments", response_model=list[CommentOut], tags=["comments"])
async def list_comments(slug: str):
    collection = get_comments_collection()
    cursor = collection.find({"fruit_slug": slug}).sort("created_at", 1)
    return [doc async for doc in cursor]


@app.post("/fruits/{slug}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED, tags=["comments"])
async def add_comment(slug: str, payload: CommentIn, _user_id: str = Depends(require_auth)):
    fruits = get_fruits_collection()
    if await fruits.find_one({"slug": slug}) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fruit not found")

    doc = {
        "fruit_slug": slug,
        "author": payload.author,
        "body": payload.body,
        "created_at": datetime.now(timezone.utc),
        "user_id": _user_id,
    }
    collection = get_comments_collection()
    result = await collection.insert_one(doc)
    return await collection.find_one({"_id": result.inserted_id})


@app.delete("/fruits/{slug}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["comments"])
async def delete_comment(slug: str, comment_id: str, _user_id: str = Depends(require_auth)):
    collection = get_comments_collection()
    result = await collection.delete_one({"_id": _to_object_id(comment_id), "fruit_slug": slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
