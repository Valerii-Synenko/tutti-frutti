import httpx

from app.config import settings


async def fetch_catalogue_summary() -> str:
    """Fetches a compact text summary of available fruits to ground the assistant's
    answers in real store data instead of letting the model invent products."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.catalogue_service_url}/fruits", params={"limit": 50})
            response.raise_for_status()
            fruits = response.json()
    except (httpx.HTTPError, ValueError):
        return "Catalogue is temporarily unavailable — do not invent product names or prices."

    if not fruits:
        return "The catalogue is currently empty."

    lines = []
    for fruit in fruits:
        organic = "organic" if fruit.get("is_organic") else "regular"
        lines.append(
            f"- {fruit['name']} (slug: {fruit['slug']}, origin: {fruit.get('origin', 'unknown')}, {organic})"
        )
    return "Fruits currently in the Tutti Frutti catalogue:\n" + "\n".join(lines)
