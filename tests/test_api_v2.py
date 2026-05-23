"""Smoke tests for the /api/v2 Smorest endpoints."""


def _login_v2(client, email, password):
    response = client.post(
        "/api/v2/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()["token"]


def test_v2_login_returns_token(client, admin):
    token = _login_v2(client, admin["email"], admin["password"])
    assert isinstance(token, str)
    assert len(token) == 64


def test_v2_login_wrong_password_returns_401(client, admin):
    response = client.post(
        "/api/v2/auth/login",
        json={"email": admin["email"], "password": "wrong"},
    )
    assert response.status_code == 401


def test_v2_list_lost_reports_pagination_envelope(client, student, sample_lost_report):
    token = _login_v2(client, student["email"], student["password"])
    response = client.get(
        "/api/v2/lost-reports",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert {"data", "page", "per_page", "total"}.issubset(body.keys())


def test_v2_create_lost_report_validates_schema(client, student):
    token = _login_v2(client, student["email"], student["password"])
    # Missing required item_name should fail marshmallow validation -> 422.
    response = client.post(
        "/api/v2/lost-reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"category": "bag"},
    )
    assert response.status_code == 422


def test_v2_openapi_spec_is_published(client):
    response = client.get("/api/v2/openapi.json")
    assert response.status_code == 200
    spec = response.get_json()
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "Lost & Found API"
    assert "/api/v2/lost-reports" in spec["paths"]
    assert "/api/v2/auth/login" in spec["paths"]


def test_v2_swagger_ui_renders(client):
    response = client.get("/api/v2/docs")
    assert response.status_code == 200
    assert b"swagger" in response.data.lower() or b"openapi" in response.data.lower()
