import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

load_dotenv()

from app.main import app
from app.database import Base, get_db

# Folosim aceeași parolă/host ca DATABASE_URL din .env, dar altă bază de date
# (shelfmatch_test), ca testele să nu atingă niciodată datele tale reale.
BASE_DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/shelfmatch")
TEST_DATABASE_URL = BASE_DB_URL.rsplit("/", 1)[0] + "/shelfmatch_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Rulează o dată per sesiune de test: creează toate tabelele, le șterge la final."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    """Client HTTP de test — orice request către `app` folosește baza de test, nu cea reală."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()