"""
Unit and integration tests for the Book resource.

Tests cover:
  - Listing an empty catalogue
  - Creating books with valid and invalid data
  - ISBN uniqueness enforcement
  - Searching the catalogue
  - Updating and deleting books
  - Preventing deletion of checked-out books
"""

import pytest


# ---------------------------------------------------------------------------
# Helper — valid book payload reused across tests
# ---------------------------------------------------------------------------

VALID_BOOK = {
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "genre": "Software Engineering",
    "published_year": 2008,
}


def post_book(client, data=None):
    """Convenience wrapper for POST /api/books."""
    return client.post("/api/books", json=data or VALID_BOOK)


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

def test_list_books_empty(client):
    """GET /api/books returns an empty list when no books exist."""
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.get_json()
    assert data["books"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# Create endpoint
# ---------------------------------------------------------------------------

def test_create_book_success(client):
    """POST /api/books with valid data returns 201 and the new book."""
    response = post_book(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == VALID_BOOK["title"]
    assert data["isbn"] == VALID_BOOK["isbn"]
    assert data["is_available"] is True


def test_create_book_missing_title(client):
    """POST /api/books without a title returns 400."""
    payload = {k: v for k, v in VALID_BOOK.items() if k != "title"}
    response = post_book(client, payload)
    assert response.status_code == 400


def test_create_book_invalid_isbn(client):
    """POST /api/books with a malformed ISBN returns 422."""
    payload = {**VALID_BOOK, "isbn": "NOT-AN-ISBN"}
    response = post_book(client, payload)
    assert response.status_code == 422
    assert "ISBN" in response.get_json()["error"]


def test_create_book_duplicate_isbn(client):
    """Creating two books with the same ISBN returns 422 on the second request."""
    post_book(client)
    response = post_book(client)  # Same ISBN
    assert response.status_code == 422
    assert "already exists" in response.get_json()["error"]


def test_create_book_future_year(client):
    """POST /api/books with a published_year in the future returns 422."""
    payload = {**VALID_BOOK, "published_year": 2999}
    response = post_book(client, payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Retrieve endpoint
# ---------------------------------------------------------------------------

def test_get_book_by_id(client):
    """GET /api/books/<id> returns the book data."""
    create_resp = post_book(client)
    book_id = create_resp.get_json()["id"]

    response = client.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.get_json()["id"] == book_id


def test_get_book_not_found(client):
    """GET /api/books/999 returns 404 when the book does not exist."""
    response = client.get("/api/books/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------

def test_search_books_by_title(client):
    """GET /api/books/search?q= returns matching books."""
    post_book(client)
    response = client.get("/api/books/search?q=clean")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert "Clean Code" in data["books"][0]["title"]


def test_search_books_no_query(client):
    """GET /api/books/search without ?q returns 400."""
    response = client.get("/api/books/search")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Update endpoint
# ---------------------------------------------------------------------------

def test_update_book_genre(client):
    """PUT /api/books/<id> can update the genre field."""
    book_id = post_book(client).get_json()["id"]
    response = client.put(f"/api/books/{book_id}", json={"genre": "Programming"})
    assert response.status_code == 200
    assert response.get_json()["genre"] == "Programming"


# ---------------------------------------------------------------------------
# Delete endpoint
# ---------------------------------------------------------------------------

def test_delete_book(client):
    """DELETE /api/books/<id> removes the book and returns 200."""
    book_id = post_book(client).get_json()["id"]
    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200

    # Verify it is gone
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_delete_book_not_found(client):
    """DELETE /api/books/999 returns 404."""
    response = client.delete("/api/books/999")
    assert response.status_code == 404


def test_delete_book_on_loan(client):
    """DELETE /api/books/<id> returns 409 when the book is currently checked out."""
    from tests.test_loans import MEMBER_PAYLOAD, BOOK_PAYLOAD

    member_id = client.post("/api/members", json=MEMBER_PAYLOAD).get_json()["id"]
    book_id = post_book(client, BOOK_PAYLOAD).get_json()["id"]
    client.post("/api/loans", json={"member_id": member_id, "book_id": book_id})

    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Additional create / update edge cases
# ---------------------------------------------------------------------------

def test_create_book_non_integer_year(client):
    """POST /api/books with a string published_year returns 422."""
    payload = {**VALID_BOOK, "isbn": "9780132350885", "published_year": "not-a-year"}
    response = post_book(client, payload)
    assert response.status_code == 422


def test_update_book_not_found(client):
    """PUT /api/books/999 returns 404."""
    response = client.put("/api/books/999", json={"genre": "Mystery"})
    assert response.status_code == 404
