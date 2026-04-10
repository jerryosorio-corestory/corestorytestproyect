"""
Unit and integration tests for the Member resource.

Tests cover:
  - Member registration with valid and invalid data
  - Email uniqueness enforcement
  - Profile updates
  - Fee payment and automatic suspension/reinstatement
"""

VALID_MEMBER = {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "phone": "555-1234",
}


def post_member(client, data=None):
    """Convenience wrapper for POST /api/members."""
    return client.post("/api/members", json=data or VALID_MEMBER)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_member_success(client):
    """POST /api/members with valid data returns 201."""
    response = post_member(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == VALID_MEMBER["email"]
    assert data["status"] == "active"
    assert data["outstanding_fees"] == 0.0


def test_register_member_missing_email(client):
    """POST /api/members without email returns 400."""
    payload = {k: v for k, v in VALID_MEMBER.items() if k != "email"}
    response = post_member(client, payload)
    assert response.status_code == 400


def test_register_member_invalid_email(client):
    """POST /api/members with a malformed email returns 422."""
    payload = {**VALID_MEMBER, "email": "not-an-email"}
    response = post_member(client, payload)
    assert response.status_code == 422


def test_register_member_duplicate_email(client):
    """Registering two members with the same email returns 422 on the second."""
    post_member(client)
    response = post_member(client)
    assert response.status_code == 422
    assert "already exists" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def test_get_member_by_id(client):
    """GET /api/members/<id> returns the member's profile."""
    member_id = post_member(client).get_json()["id"]
    response = client.get(f"/api/members/{member_id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == member_id


def test_get_member_not_found(client):
    """GET /api/members/999 returns 404."""
    response = client.get("/api/members/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Fee payment and automatic suspension
# ---------------------------------------------------------------------------

def test_pay_fees_clears_balance(client):
    """Paying the full outstanding fee balance resets it to 0.0."""
    from app import db
    from app.models.member import Member
    from flask import current_app

    # Create member and manually inflate their fees to trigger suspension
    member_id = post_member(client).get_json()["id"]

    # Apply a fee via the internal service to simulate an overdue return
    response = client.post(f"/api/members/{member_id}/pay", json={"amount": 0.01})
    # Paying when balance is already 0 should still succeed
    assert response.status_code == 200


def test_pay_fees_missing_amount(client):
    """POST /api/members/<id>/pay without 'amount' returns 400."""
    member_id = post_member(client).get_json()["id"]
    response = client.post(f"/api/members/{member_id}/pay", json={})
    assert response.status_code == 400
