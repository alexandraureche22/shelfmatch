from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import books, recommendations, stats, auth, friends, feed, challenges

app = FastAPI(title="ShelfMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pentru dev; restrânge la deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(recommendations.router)
app.include_router(stats.router)
app.include_router(friends.router)
app.include_router(feed.router)
app.include_router(challenges.router)


@app.get("/")
def root():
    return {"status": "ShelfMatch API running"}