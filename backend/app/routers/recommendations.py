from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, google_books, models, auth
from ..database import get_db

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=list[schemas.RecommendationOut])
async def get_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    limit: int = 5,
):
    """
    1. Ia genurile cu rating mediu cel mai mare din istoricul user-ului curent.
    2. Caută cărți noi din acele genuri prin Google Books, excluzând ce a citit deja.
    3. Pentru fiecare, estimează câte zile i-ar lua, pe baza ritmului lui mediu pe acel gen.
    """
    top_genres = crud.get_top_genres(db, current_user.id, limit=3)
    if not top_genres:
        return []

    already_read = crud.get_read_google_ids(db, current_user.id)
    genre_stats = {row["genre"]: row for row in crud.get_genre_stats(db, current_user.id)}

    recommendations = []
    for genre in top_genres:
        candidates = await google_books.search_by_genre(genre, already_read, max_results=2)
        pace = genre_stats.get(genre, {}).get("avg_pages_per_day")

        for c in candidates:
            estimated_days = None
            if pace and c.get("pages"):
                estimated_days = round(c["pages"] / pace, 1)
            recommendations.append(schemas.RecommendationOut(
                **c,
                estimated_days_to_read=estimated_days,
            ))

    return recommendations[:limit]


@router.get("/estimate")
def estimate_reading_time(
    pages: int,
    genre: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Estimare rapidă: cât timp i-ar lua user-ului curent o carte cu X pagini dintr-un gen dat."""
    stats = {row["genre"]: row for row in crud.get_genre_stats(db, current_user.id)}
    pace = stats.get(genre, {}).get("avg_pages_per_day")

    if not pace:
        all_paces = [r["avg_pages_per_day"] for r in stats.values() if r["avg_pages_per_day"]]
        pace = sum(all_paces) / len(all_paces) if all_paces else None

    if not pace:
        return {"estimated_days": None, "message": "There's not enough data to estimate your reading pace yet."}

    return {"estimated_days": round(pages / pace, 1), "pace_used": round(pace, 2)}