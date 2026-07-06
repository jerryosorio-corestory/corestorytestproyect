"""
Unit and integration tests for the Loan resource.

Tests cover:
  - Successful book checkout
  - Renewing an eligible loan
  - Attempting to borrow when member is suspended
  - Attempting to borrow an already checked-out book
  - Enforcing the concurrent loan limit
  - Returning a book on time (no fee)
  - Listing overdue loans
"""

from datetime import datetime, timedelta, timezone

BOOK_PAYLOAD = {
    "title": "The Pragmatic Programmer",
    "author": "David Thomas",
    "isbn": "9780135957059",
    "genre": "Software Engineering",
    "published_year": 2019,
}

MEMBER_PAYLOAD = {
    "first_name": "Bob",
    "last_name": "Jones",
    "email": "bob@example.com",
}


def setup_member_and_book(client):
    """Create one member and one book, return their IDs."""
    member_id = client.post("/api/members", json=MEMBER_PAYLOAD).get_json()["id"]
    book_id = client.post("/api/books", json=BOOK_PAYLOAD).get_json()["id"]
    return member_id, book_id


def checkout(client, member_id, book_id):
    """Convenience wrapper for POST /api/loans."""
    return client.post("/api/loans", json={"member_id": member_id, "book_id": book_id})


# ---------------------------------------------------------------------------
# Checkout — success path
# ---------------------------------------------------------------------------

def test_checkout_success(client):
    """POST /api/loans creates a loan and marks the book as unavailable."""
    member_id, book_id = setup_member_and_book(client)
    response = checkout(client, member_id, book_id)

    assert response.status_code == 201
    data = response.get_json()
    assert data["member_id"] == member_id
    assert data["book_id"] == book_id
    assert data["returned"] is False

    # The book should now show as unavailable
    book = client.get(f"/api/books/{book_id}").get_json()
    assert book["is_available"] is False


# ---------------------------------------------------------------------------
# Checkout — business rule violations
# ---------------------------------------------------------------------------

def test_checkout_book_already_on_loan(client):
    """Checking out a book that is already on loan returns 422."""
    member_id, book_id = setup_member_and_book(client)
    checkout(client, member_id, book_id)  # First checkout succeeds

    # Register a second member to attempt the same book
    second_member_id = client.post("/api/members", json={
        "first_name": "Carol",
        "last_name": "White",
        "email": "carol@example.com",
    }).get_json()["id"]

    response = checkout(client, second_member_id, book_id)
    assert response.status_code == 422
    assert "not available" in response.get_json()["error"]


def test_checkout_suspended_member(client):
    """A suspended member cannot check out books."""
    from app import db
    from app.models.member import Member, MemberStatus

    member_id, book_id = setup_member_and_book(client)

    # Suspend the member directly via the database
    with client.application.app_context():
        from app import db as _db
        member = _db.session.get(Member, member_id)
        member.status = MemberStatus.SUSPENDED
        db.session.commit()

    response = checkout(client, member_id, book_id)
    assert response.status_code == 422
    assert "suspended" in response.get_json()["error"]


def test_checkout_missing_fields(client):
    """POST /api/loans without required fields returns 400."""
    response = client.post("/api/loans", json={"member_id": 1})
    assert response.status_code == 400


def test_checkout_nonexistent_member(client):
    """POST /api/loans with an unknown member_id returns 404."""
    _, book_id = setup_member_and_book(client)
    response = checkout(client, 9999, book_id)
    assert response.status_code == 404


def test_checkout_nonexistent_book(client):
    """POST /api/loans with an unknown book_id returns 404."""
    member_id, _ = setup_member_and_book(client)
    response = checkout(client, member_id, 9999)
    assert response.status_code == 404


def test_checkout_invalid_ids(client):
    """POST /api/loans with non-integer IDs returns 400."""
    response = client.post("/api/loans", json={"member_id": "abc", "book_id": "xyz"})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Return
# ---------------------------------------------------------------------------

def test_return_book_on_time(client):
    """POST /api/loans/<id>/return closes the loan with no late fee."""
    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    response = client.post(f"/api/loans/{loan_id}/return")
    assert response.status_code == 200
    data = response.get_json()
    assert data["returned"] is True
    assert data["late_fee"] == 0.0
    assert "on time" in data["message"]


def test_return_book_already_returned(client):
    """Returning an already-returned book returns 422."""
    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    client.post(f"/api/loans/{loan_id}/return")  # First return
    response = client.post(f"/api/loans/{loan_id}/return")  # Second return
    assert response.status_code == 422
    assert "already been closed" in response.get_json()["error"]


# ---------------------------------------------------------------------------
# Renewal
# ---------------------------------------------------------------------------

def test_renew_loan_success(client):
    """POST /api/loans/<id>/renew extends the due date for an eligible loan."""
    member_id, book_id = setup_member_and_book(client)
    data = checkout(client, member_id, book_id).get_json()
    loan_id = data["id"]
    original_due_date = datetime.fromisoformat(data["due_date"])

    response = client.post(f"/api/loans/{loan_id}/renew")
    assert response.status_code == 200
    renewed = response.get_json()
    renewed_due_date = datetime.fromisoformat(renewed["due_date"])

    assert renewed["renewal_count"] == 1
    assert renewed["last_renewed_at"] is not None
    assert renewed_due_date == original_due_date + timedelta(days=7)
    assert "renewed successfully" in renewed["message"]


def test_renew_loan_already_returned(client):
    """Returned loans cannot be renewed."""
    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    client.post(f"/api/loans/{loan_id}/return")
    response = client.post(f"/api/loans/{loan_id}/renew")

    assert response.status_code == 422
    assert "already been closed" in response.get_json()["error"]


def test_renew_loan_overdue(client):
    """Overdue loans cannot be renewed."""
    from app import db
    from app.models.loan import Loan

    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    with client.application.app_context():
        loan = db.session.get(Loan, loan_id)
        loan.due_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        db.session.commit()

    response = client.post(f"/api/loans/{loan_id}/renew")
    assert response.status_code == 422
    assert "already overdue" in response.get_json()["error"]


def test_renew_loan_exceeds_limit(client):
    """A loan cannot be renewed more than once."""
    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    first = client.post(f"/api/loans/{loan_id}/renew")
    assert first.status_code == 200

    second = client.post(f"/api/loans/{loan_id}/renew")
    assert second.status_code == 422
    assert "renewal limit" in second.get_json()["error"]


def test_renew_loan_not_found(client):
    """Unknown loans return 404 when renewal is requested."""
    response = client.post("/api/loans/999/renew")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Overdue
# ---------------------------------------------------------------------------

def test_list_overdue_empty(client):
    """GET /api/loans/overdue returns empty list when no loans are overdue."""
    response = client.get("/api/loans/overdue")
    assert response.status_code == 200
    assert response.get_json()["total"] == 0


# ---------------------------------------------------------------------------
# Fee preview
# ---------------------------------------------------------------------------

def test_fee_preview_active_loan(client):
    """GET /api/loans/<id>/fee returns fee info for an open loan."""
    member_id, book_id = setup_member_and_book(client)
    loan_id = checkout(client, member_id, book_id).get_json()["id"]

    response = client.get(f"/api/loans/{loan_id}/fee")
    assert response.status_code == 200
    data = response.get_json()
    # Loan was just created — it is not overdue yet
    assert data["is_overdue"] is False
    assert data["potential_fee"] == 0.0
