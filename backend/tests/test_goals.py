def _get_auth_headers(client, email="test_goal_user@example.com"):
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/auth/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_set_and_get_goal(client):
    headers = _get_auth_headers(client)

    resp = client.post("/goals/", headers=headers, json={"target": 12})
    assert resp.status_code == 200
    assert resp.json()["target"] == 12

    resp2 = client.get("/goals/current", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["target"] == 12
    assert resp2.json()["finished_count"] == 0


def test_goal_counts_finished_books(client):
    headers = _get_auth_headers(client, email="test_goal_progress@example.com")
    client.post("/goals/", headers=headers, json={"target": 5})

    book_resp = client.post("/books/", json={"title": "Finished Book", "pages": 100})
    book_id = book_resp.json()["id"]
    client.post("/books/log", headers=headers, json={
        "book_id": book_id,
        "status": "finished",
        "rating": 4,
    })

    resp = client.get("/goals/current", headers=headers)
    assert resp.json()["finished_count"] == 1