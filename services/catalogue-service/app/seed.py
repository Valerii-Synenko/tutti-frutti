"""
Seeds the catalogue with demo fruit data. Run manually:
    python -m app.seed
Deliberately uses irregular `attributes` per fruit to demonstrate why this
collection benefits from MongoDB's flexible schema instead of a rigid table.
"""

import asyncio

from app.database import ensure_indexes, get_fruits_collection

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


async def main() -> None:
    await ensure_indexes()
    collection = get_fruits_collection()
    for fruit in FRUITS:
        await collection.update_one({"slug": fruit["slug"]}, {"$set": fruit}, upsert=True)
    print(f"Seeded {len(FRUITS)} fruits.")


if __name__ == "__main__":
    asyncio.run(main())
