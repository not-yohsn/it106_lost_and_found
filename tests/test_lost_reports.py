"""Lost-report CRUD + privacy filter tests."""


def test_list_lost_reports_returns_pagination_envelope(client, auth_student, sample_lost_report):
    response = client.get("/api/v1/lost-reports", headers=auth_student)
    assert response.status_code == 200
    body = response.get_json()
    assert "data" in body
    assert "page" in body
    assert "per_page" in body
    assert "total" in body
    assert isinstance(body["data"], list)


def test_owner_sees_full_payload_on_own_report(client, auth_student, sample_lost_report):
    response = client.get(
        f"/api/v1/lost-reports/{sample_lost_report}", headers=auth_student
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["description"] == "Has my laptop inside."
    assert data["location"] == "Library 2F"


def test_non_owner_student_sees_filtered_payload(client, auth_student2, sample_lost_report):
    """Privacy filter: a different student must NOT see description or location."""
    response = client.get(
        f"/api/v1/lost-reports/{sample_lost_report}", headers=auth_student2
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert "item_name" in data
    assert data.get("description") in (None, "")
    assert data.get("location") in (None, "")


def test_create_lost_report_succeeds(client, auth_student):
    response = client.post(
        "/api/v1/lost-reports",
        headers=auth_student,
        json={
            "item_name": "Silver Pen",
            "category": "stationery",
            "location": "Cafeteria table 4",
            "date_lost": "2026-05-17",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["item_name"] == "Silver Pen"


def test_update_lost_report_persists_changes(client, auth_student, sample_lost_report):
    response = client.put(
        f"/api/v1/lost-reports/{sample_lost_report}",
        headers=auth_student,
        json={"description": "Has my ID card inside"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["description"] == "Has my ID card inside"


def test_delete_lost_report_returns_204(client, auth_student, sample_lost_report):
    response = client.delete(
        f"/api/v1/lost-reports/{sample_lost_report}", headers=auth_student
    )
    assert response.status_code == 204
    assert response.data == b""
