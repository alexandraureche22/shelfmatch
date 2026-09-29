def test_register_and_login(client):
    email = "test_register@example.com"
    resp = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == email
    assert "access_token" in data

    resp2 = client.post("/auth/login", json={"email": email, "password": "secret123"})
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


def test_login_wrong_password(client):
    email = "test_wrongpass@example.com"
    client.post("/auth/register", json={"email": email, "password": "secret123"})

    resp = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


def test_register_duplicate_email(client):
    email = "test_dup@example.com"
    client.post("/auth/register", json={"email": email, "password": "secret123"})

    resp = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 400


def test_protected_route_requires_token(client):
    resp = client.get("/books/mine")
    assert resp.status_code == 401