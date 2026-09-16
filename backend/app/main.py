from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import books, recommendations, stats

app = FastAPI(title="ShelfMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pentru dev; restrânge la deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(recommendations.router)
app.include_router(stats.router)


@app.get("/")
def root():
    return {"status": "ShelfMatch API running"}
