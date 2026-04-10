"""
Book API endpoints — mounted at /api/books

Provides full CRUD plus a search endpoint for the book catalogue.

Endpoints:
  GET    /api/books              — list all books
  POST   /api/books              — add a new book
  GET    /api/books/search       — search books by title, author, or ISBN
  GET    /api/books/<id>         — get a single book
  PUT    /api/books/<id>         — update a book
  DELETE /api/books/<id>         — remove a book
"""

from flask import Blueprint, request, jsonify
from app.services.book_service import BookService

# Blueprint groups all book-related routes under a common prefix
books_bp = Blueprint("books", __name__)


@books_bp.route("", methods=["GET"])
def list_books():
    """
    GET /api/books
    Returns all books in the catalogue ordered by title.
    """
    books = BookService.get_all()
    result = [_book_to_dict(b) for b in books]
    return jsonify({"books": result, "total": len(result)}), 200


@books_bp.route("/search", methods=["GET"])
def search_books():
    """
    GET /api/books/search?q=<query>
    Search books by title, author, or ISBN (case-insensitive partial match).

    Query params:
      q (required) — search term
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    books = BookService.search(query)
    result = [_book_to_dict(b) for b in books]
    return jsonify({"books": result, "total": len(result), "query": query}), 200


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id: int):
    """
    GET /api/books/<book_id>
    Retrieve a single book by its ID.

    Path params:
      book_id — integer primary key of the book
    """
    book = BookService.get_by_id(book_id)
    if not book:
        return jsonify({"error": f"Book with id {book_id} not found"}), 404

    return jsonify(_book_to_dict(book)), 200


@books_bp.route("", methods=["POST"])
def create_book():
    """
    POST /api/books
    Add a new book to the catalogue.

    Request body (JSON):
      title          (required) — book title
      author         (required) — author full name
      isbn           (required) — ISBN-10 or ISBN-13
      genre          (optional) — genre label
      published_year (optional) — integer year of publication
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Check required fields before calling the service
    for field in ("title", "author", "isbn"):
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400

    book, error = BookService.create(data)
    if error:
        return jsonify({"error": error}), 422

    return jsonify(_book_to_dict(book)), 201


@books_bp.route("/<int:book_id>", methods=["PUT"])
def update_book(book_id: int):
    """
    PUT /api/books/<book_id>
    Update one or more fields of an existing book.

    Path params:
      book_id — integer primary key of the book

    Request body (JSON) — all fields optional:
      title, author, genre, published_year
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    book, error = BookService.update(book_id, data)
    if error:
        status = 404 if "not found" in error else 422
        return jsonify({"error": error}), status

    return jsonify(_book_to_dict(book)), 200


@books_bp.route("/<int:book_id>", methods=["DELETE"])
def delete_book(book_id: int):
    """
    DELETE /api/books/<book_id>
    Remove a book from the catalogue.

    Returns 409 Conflict if the book is currently on loan.
    """
    error = BookService.delete(book_id)
    if error:
        status = 404 if "not found" in error else 409
        return jsonify({"error": error}), status

    return jsonify({"message": f"Book {book_id} deleted successfully"}), 200


def _book_to_dict(book) -> dict:
    """Convert a Book ORM object to a JSON-serialisable dictionary."""
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "genre": book.genre,
        "published_year": book.published_year,
        "is_available": book.is_available,
        "created_at": book.created_at.isoformat() if book.created_at else None,
    }
