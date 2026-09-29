import pytest
import uuid


@pytest.fixture
def auth_headers(client):
    """Creează un cont nou (email unic de fiecare dată) și întoarce header-ul de autentificare."""
    email = f"test_books_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/auth/register", json={"email": email, "password": "secret123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_add_book_and_log(client, auth_headers):
    book_resp = client.post("/books/", json={
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "pages": 200,
    })
    assert book_resp.status_code == 200
    book_id = book_resp.json()["id"]

    log_resp = client.post("/books/log", headers=auth_headers, json={
        "book_id": book_id,
        "status": "reading",
    })
    assert log_resp.status_code == 200
    assert log_resp.json()["status"] == "reading"


def test_edit_and_delete_entry(client, auth_headers):
    book_resp = client.post("/books/", json={"title": "Edit Me", "pages": 100})
    book_id = book_resp.json()["id"]

    log_resp = client.post("/books/log", headers=auth_headers, json={"book_id": book_id, "status": "wishlist"})
    entry_id = log_resp.json()["id"]

    edit_resp = client.put(f"/books/log/{entry_id}", headers=auth_headers, json={"status": "finished", "rating": 5})
    assert edit_resp.status_code == 200
    assert edit_resp.json()["rating"] == 5
    assert edit_resp.json()["status"] == "finished"

    delete_resp = client.delete(f"/books/log/{entry_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    # cartea nu mai trebuie să apară în listă după ștergere
    mine_resp = client.get("/books/mine", headers=auth_headers)
    ids = [e["id"] for e in mine_resp.json()]
    assert entry_id not in ids


def test_cannot_edit_someone_elses_entry(client):
    # user 1 adaugă o carte
    client.post("/auth/register", json={"email": "owner@example.com", "password": "secret123"})
    login1 = client.post("/auth/login", json={"email": "owner@example.com", "password": "secret123"})
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    book_resp = client.post("/books/", json={"title": "Private Book", "pages": 150})
    book_id = book_resp.json()["id"]
    log_resp = client.post("/books/log", headers=headers1, json={"book_id": book_id, "status": "reading"})
    entry_id = log_resp.json()["id"]

    # user 2 încearcă să editeze cartea lui user 1
    client.post("/auth/register", json={"email": "intruder@example.com", "password": "secret123"})
    login2 = client.post("/auth/login", json={"email": "intruder@example.com", "password": "secret123"})
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    resp = client.put(f"/books/log/{entry_id}", headers=headers2, json={"status": "finished"})
    assert resp.status_code == 404