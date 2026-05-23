"""Authorization (403) + error-envelope (404) tests."""


def test_unknown_api_route_returns_json_404(client, auth_admin):
    response = client.get("/api/v1/no-such-route", headers=auth_admin)
    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"] == "not_found"


def test_student_cannot_delete_found_item_returns_403(client, auth_student, sample_found_item):
    response = client.delete(
        f"/api/v1/found-items/{sample_found_item}", headers=auth_student
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == "forbidden"
