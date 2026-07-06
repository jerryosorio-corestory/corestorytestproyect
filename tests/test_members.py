"""
Unit and integration tests for the Member resource.

Tests cover:
  - Member registration with valid and invalid data
  - Email uniqueness enforcement
  - Profile updates
  - Fee payment validation and automatic suspension/reinstatement
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
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]

    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 5.00)

    response = client.post(f"/api/members/{member_id}/pay", json={"amount": 5.00})
    assert response.status_code == 200
    member = response.get_json()["member"]
    assert member["outstanding_fees"] == 0.0
    assert member["status"] == "active"


def test_pay_fees_missing_amount(client):
    """POST /api/members/<id>/pay without 'amount' returns 400."""
    member_id = post_member(client).get_json()["id"]
    response = client.post(f"/api/members/{member_id}/pay", json={})
    assert response.status_code == 400


def test_pay_fees_negative_amount(client):
    """POST /api/members/<id>/pay with a negative amount returns 422."""
    member_id = post_member(client).get_json()["id"]
    response = client.post(f"/api/members/{member_id}/pay", json={"amount": -5.0})
    assert response.status_code == 422


def test_pay_fees_overpayment_rejected(client):
    """POST /api/members/<id>/pay rejects payments above the outstanding balance."""
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]

    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 3.00)

    response = client.post(f"/api/members/{member_id}/pay", json={"amount": 5.00})
    assert response.status_code == 422
    assert "exceeds outstanding balance" in response.get_json()["error"]


def test_pay_fees_partial_payment_keeps_remaining_balance(client):
    """Partial payments reduce the balance without reactivating a suspended member."""
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]

    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 5.00)

    response = client.post(f"/api/members/{member_id}/pay", json={"amount": 2.00})
    assert response.status_code == 200
    member = response.get_json()["member"]
    assert member["outstanding_fees"] == 3.0
    assert member["status"] == "suspended"


# ---------------------------------------------------------------------------
# Auto-suspension and reinstatement
# ---------------------------------------------------------------------------

def test_auto_suspension_on_fee_threshold(client):
    """Member is suspended when outstanding fees reach the $5.00 threshold."""
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]

    # Apply a fee large enough to trigger automatic suspension
    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 5.00)

    response = client.get(f"/api/members/{member_id}")
    data = response.get_json()
    assert data["status"] == "suspended"
    assert data["outstanding_fees"] == 5.00


def test_auto_reinstatement_on_full_payment(client):
    """Paying off all outstanding fees reactivates a suspended member."""
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]

    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 5.00)

    client.post(f"/api/members/{member_id}/pay", json={"amount": 5.00})

    response = client.get(f"/api/members/{member_id}")
    data = response.get_json()
    assert data["status"] == "active"
    assert data["outstanding_fees"] == 0.0


# ---------------------------------------------------------------------------
# List members
# ---------------------------------------------------------------------------

def test_list_members_returns_all(client):
    """GET /api/members returns every registered member."""
    post_member(client)
    post_member(client, {**VALID_MEMBER, "email": "bob@example.com", "first_name": "Bob"})
    response = client.get("/api/members")
    assert response.status_code == 200
    assert response.get_json()["total"] == 2


def test_list_members_filter_by_status(client):
    """GET /api/members?status=suspended returns only suspended members."""
    from app.services.member_service import MemberService

    member_id = post_member(client).get_json()["id"]
    post_member(client, {**VALID_MEMBER, "email": "bob@example.com", "first_name": "Bob"})

    with client.application.app_context():
        MemberService.apply_late_fee(member_id, 5.00)

    response = client.get("/api/members?status=suspended")
    data = response.get_json()
    assert data["total"] == 1
    assert data["members"][0]["id"] == member_id


def test_list_members_filter_invalid_status(client):
    """GET /api/members?status=unknown returns 400."""
    response = client.get("/api/members?status=unknown")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Update member
# ---------------------------------------------------------------------------

def test_update_member_name(client):
    """PUT /api/members/<id> updates first and last name."""
    member_id = post_member(client).get_json()["id"]
    response = client.put(f"/api/members/{member_id}", json={"first_name": "Alicia"})
    assert response.status_code == 200
    assert response.get_json()["first_name"] == "Alicia"


def test_update_member_email_to_existing_raises_422(client):
    """PUT /api/members/<id> cannot change email to one already used."""
    post_member(client, {**VALID_MEMBER, "email": "bob@example.com", "first_name": "Bob"})
    alice_id = post_member(client).get_json()["id"]
    response = client.put(f"/api/members/{alice_id}", json={"email": "bob@example.com"})
    assert response.status_code == 422


def test_update_member_not_found(client):
    """PUT /api/members/999 returns 404."""
    response = client.put("/api/members/999", json={"first_name": "Ghost"})
    assert response.status_code == 404
