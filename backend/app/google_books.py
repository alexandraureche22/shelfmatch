import os
import httpx

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


async def search_books(query: str, max_results: int = 10) -> list[dict]:
    """Caută cărți prin Google Books API și normalizează câmpurile utile.
    Lasă eroarea să urce (nu o ascunde), ca ruta care apelează asta să poată răspunde clar."""
    params = {"q": query, "maxResults": max_results}
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GOOGLE_BOOKS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        results.append({
            "google_books_id": item.get("id"),
            "title": info.get("title", "Titlu necunoscut"),
            "author": ", ".join(info.get("authors", [])) or None,
            "genre": (info.get("categories") or [None])[0],
            "pages": info.get("pageCount"),
            "cover_url": info.get("imageLinks", {}).get("thumbnail"),
        })
    return results


async def search_by_genre(genre: str, exclude_ids: set[str], max_results: int = 5) -> list[dict]:
    """Caută cărți noi într-un gen dat, excluzând ce ai citit deja (pt recomandări).
    Aici sărim silențios peste erori — un gen care eșuează nu trebuie să strice toată lista de recomandări."""
    try:
        candidates = await search_books(f"subject:{genre}", max_results=max_results + len(exclude_ids))
    except httpx.HTTPStatusError:
        return []
    filtered = [c for c in candidates if c["google_books_id"] not in exclude_ids]
    return filtered[:max_results]