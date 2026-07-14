"""
Seeds the catalogue with demo fruit data. Run manually:
    python -m app.seed
Deliberately uses irregular `attributes` per fruit to demonstrate why this
collection benefits from MongoDB's flexible schema instead of a rigid table.
"""

import asyncio
from datetime import datetime, timezone

from app.database import ensure_indexes, get_comments_collection, get_fruits_collection

FRUITS = [
    {
        "name": "Pink Lady Apple",
        "slug": "pink-lady-apple",
        "description": "Crisp, sweet-tart apple with a rosy blush.",
        "origin": "Italy",
        "is_organic": True,
        "seasonal_months": [9, 10, 11, 12, 1],
        "tags": ["crisp", "snack", "lunchbox"],
        "image_url": "/images/pink-lady-apple.svg",
        "base_price_hint_eur": 0.60,
        "attributes": {"shelf_life_days": 45, "storage": "refrigerated", "allergen_notes": None},
    },
    {
        "name": "Alphonso Mango",
        "slug": "alphonso-mango",
        "description": "The 'king of mangoes' — intensely aromatic and silky.",
        "origin": "India",
        "is_organic": False,
        "seasonal_months": [4, 5, 6],
        "tags": ["tropical", "smoothie", "premium"],
        "image_url": "/images/alphonso-mango.svg",
        "base_price_hint_eur": 3.20,
        "attributes": {
            "ripening_climate": "tropical",
            "ripens_after_harvest": True,
            "average_weight_g": 250,
        },
    },
    {
        "name": "Wild Blueberries",
        "slug": "wild-blueberries",
        "description": "Small, intensely flavoured wild-harvested blueberries.",
        "origin": "Finland",
        "is_organic": True,
        "seasonal_months": [7, 8],
        "tags": ["berry", "antioxidant", "smoothie"],
        "image_url": "/images/wild-blueberries.svg",
        "base_price_hint_eur": 4.50,
        "attributes": {"shelf_life_days": 7, "pack_size_g": 125, "freezes_well": True},
    },
    {
        "name": "Dragon Fruit",
        "slug": "dragon-fruit",
        "description": "Striking pink skin, mildly sweet speckled white flesh.",
        "origin": "Vietnam",
        "is_organic": False,
        "seasonal_months": [6, 7, 8, 9],
        "tags": ["exotic", "instagrammable"],
        "image_url": "/images/dragon-fruit.svg",
        "base_price_hint_eur": 2.90,
        "attributes": {"variety": "Hylocereus undatus", "edible_skin": False},
    },
    {
        "name": "Croatian Fig",
        "slug": "croatian-fig",
        "description": "Sun-ripened figs from the Dalmatian coast.",
        "origin": "Croatia",
        "is_organic": True,
        "seasonal_months": [8, 9],
        "tags": ["local", "premium", "dessert"],
        "image_url": "/images/croatian-fig.svg",
        "base_price_hint_eur": 5.00,
        "attributes": {"shelf_life_days": 3, "handle_with_care": True},
    },
    {
        "name": "Cavendish Banana",
        "slug": "cavendish-banana",
        "description": "The everyday banana — reliable, sweet, portable.",
        "origin": "Ecuador",
        "is_organic": False,
        "seasonal_months": list(range(1, 13)),
        "tags": ["everyday", "lunchbox", "kids"],
        "image_url": "/images/cavendish-banana.svg",
        "base_price_hint_eur": 0.35,
        "attributes": {"sold_by": "bunch", "ripening_stage_tracked": True},
    },
    {
        "name": "Kherson Watermelon",
        "slug": "kherson-watermelon",
        "description": "Legendary sweet, juicy watermelon from the sun-baked "
        "fields of Kherson, southern Ukraine.",
        "origin": "Ukraine",
        "is_organic": True,
        "seasonal_months": [8, 9],
        "tags": ["local", "summer", "juicy", "iconic"],
        "image_url": "/images/kherson-watermelon.svg",
        "base_price_hint_eur": 1.80,
        "attributes": {"sold_by": "whole", "average_weight_kg": 8, "seedless": False},
    },
]


def _dt(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


COMMENTS = [
    {"fruit_slug": "pink-lady-apple", "author": "Maria K.", "body": "Perfect for my kids' lunchboxes — crunchy and not too sweet!", "created_at": _dt(2025, 6, 10, 9)},
    {"fruit_slug": "pink-lady-apple", "author": "Tom B.", "body": "My go-to apple. Keeps well in the fridge for weeks.", "created_at": _dt(2025, 6, 15, 14)},
    {"fruit_slug": "alphonso-mango", "author": "Priya S.", "body": "The real Alphonso! So fragrant, brings back memories of home 🥭", "created_at": _dt(2025, 5, 20, 11)},
    {"fruit_slug": "alphonso-mango", "author": "Leo F.", "body": "Expensive but worth every cent. Absolutely divine.", "created_at": _dt(2025, 5, 22, 18)},
    {"fruit_slug": "wild-blueberries", "author": "Anna L.", "body": "Way more flavourful than the cultivated ones. Freeze them for smoothies!", "created_at": _dt(2025, 7, 5, 8)},
    {"fruit_slug": "wild-blueberries", "author": "Erik J.", "body": "Straight from the Finnish forest. Nothing beats it.", "created_at": _dt(2025, 7, 8, 16)},
    {"fruit_slug": "dragon-fruit", "author": "Jake R.", "body": "Looks incredible on a fruit platter. Taste is mild but unique.", "created_at": _dt(2025, 6, 28, 16)},
    {"fruit_slug": "dragon-fruit", "author": "Mei C.", "body": "Love the texture! Great in a smoothie bowl.", "created_at": _dt(2025, 7, 1, 10)},
    {"fruit_slug": "croatian-fig", "author": "Iva M.", "body": "Dalmatian figs are unlike anything else. Handle with care — very delicate.", "created_at": _dt(2025, 8, 3, 10)},
    {"fruit_slug": "croatian-fig", "author": "Sven H.", "body": "Paired with prosciutto and gorgonzola — absolutely stunning.", "created_at": _dt(2025, 8, 5, 20)},
    {"fruit_slug": "cavendish-banana", "author": "Sofia P.", "body": "Reliable, affordable, and kids love them. A staple in our house.", "created_at": _dt(2025, 6, 1, 7)},
    {"fruit_slug": "cavendish-banana", "author": "Dan W.", "body": "Great for pre-workout. Always keep a bunch on the counter.", "created_at": _dt(2025, 6, 10, 6)},
    {"fruit_slug": "kherson-watermelon", "author": "Oleh V.", "body": "These are legendary in Ukraine for a reason. Incredibly sweet!", "created_at": _dt(2025, 8, 12, 15)},
    {"fruit_slug": "kherson-watermelon", "author": "Dana K.", "body": "Bought a whole one and shared it with the whole family. Worth it!", "created_at": _dt(2025, 8, 14, 12)},
]


async def main() -> None:
    await ensure_indexes()

    fruits_col = get_fruits_collection()
    for fruit in FRUITS:
        await fruits_col.update_one({"slug": fruit["slug"]}, {"$set": fruit}, upsert=True)
    print(f"Seeded {len(FRUITS)} fruits.")

    comments_col = get_comments_collection()
    for comment in COMMENTS:
        exists = await comments_col.find_one({"fruit_slug": comment["fruit_slug"], "author": comment["author"], "body": comment["body"]})
        if exists is None:
            await comments_col.insert_one(comment)
    print(f"Seeded {len(COMMENTS)} comments.")


if __name__ == "__main__":
    asyncio.run(main())
