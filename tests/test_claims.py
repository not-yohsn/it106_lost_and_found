"""Claim state-machine tests — enforces _ALLOWED_TRANSITIONS."""


def test_admin_can_approve_pending_claim(client, auth_admin, sample_match_and_claim):
    claim_id = sample_match_and_claim["claim_id"]
    response = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=auth_admin,
        json={"status": "approved"},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["status"] == "approved"
    assert data["verified_by"] is not None
    assert data["resolved_at"] is not None


def test_invalid_transition_approved_to_pending_returns_400(client, auth_admin, sample_match_and_claim):
    claim_id = sample_match_and_claim["claim_id"]

    approve = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=auth_admin,
        json={"status": "approved"},
    )
    assert approve.status_code == 200

    # Now try to reverse it
    response = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=auth_admin,
        json={"status": "pending"},
    )
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "invalid_transition"
    assert "cannot move from approved to pending" in body["fields"]["status"]


def test_unknown_status_value_returns_400(client, auth_admin, sample_match_and_claim):
    claim_id = sample_match_and_claim["claim_id"]
    response = client.put(
        f"/api/v1/claims/{claim_id}",
        headers=auth_admin,
        json={"status": "weird"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "validation_failed"


def test_student_sees_only_own_claims(client, auth_student, auth_student2, sample_match_and_claim):
    response_own = client.get("/api/v1/claims", headers=auth_student)
    assert response_own.status_code == 200
    assert len(response_own.get_json()["data"]) == 1

    response_other = client.get("/api/v1/claims", headers=auth_student2)
    assert response_other.status_code == 200
    assert response_other.get_json()["data"] == []
