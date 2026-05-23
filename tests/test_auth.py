"""Authentication endpoint tests (login, logout, token validation)."""


def test_login_success_returns_token(client, admin):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin["email"], "password": admin["password"]},
    )
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert "token" in body
    assert len(body["token"]) == 64
    assert body["user"]["email"] == admin["email"]


def test_login_wrong_password_returns_401(client, admin):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin["email"], "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "invalid_credentials"


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.local", "password": "whatever"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "invalid_credentials"


def test_logout_returns_204_and_invalidates_token(client, auth_student, student):
    logout = client.post("/api/v1/auth/logout", headers=auth_student)
    assert logout.status_code == 204

    follow_up = client.get("/api/v1/me", headers=auth_student)
    assert follow_up.status_code == 401
    assert follow_up.get_json()["error"] == "authentication_required"


def test_protected_endpoint_without_header_returns_401(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 401
    assert response.get_json()["error"] == "authentication_required"


def test_me_endpoint_returns_current_user(client, auth_admin, admin):
    response = client.get("/api/v1/me", headers=auth_admin)
    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == admin["email"]
