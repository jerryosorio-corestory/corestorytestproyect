"""
BookService — business logic for managing the book catalogue.

Responsibilities:
  - Create, read, update, and delete book records
  - Enforce uniqueness of ISBNs
  - Validate catalogue fields before persisting
"""

from typing import List, Optional, Dict, Any
from app import db
from app.models.book import Book
from app.utils.validators import validate_isbn, validate_year


class BookService:
    """Stateless service class — all methods are class-level for easy testing."""

    @classmethod
    def get_all(cls) -> List[Book]:
        """Return every book in the catalogue, ordered by title."""
        return Book.query.order_by(Book.title).all()

    @classmethod
    def get_by_id(cls, book_id: int) -> Optional[Book]:
        """
        Fetch a single book by its primary key.

        Returns None if no book with that ID exists (callers handle the 404).
        """
        return db.session.get(Book, book_id)

    @classmethod
    def search(cls, query: str) -> List[Book]:
        """
        Full-text search across title, author, and ISBN fields.

        Uses SQL LIKE with wildcards — suitable for small libraries.
        For larger datasets this should be replaced with a proper FTS index.
        """
        wildcard = f"%{query}%"
        return (
            Book.query.filter(
                db.or_(
                    Book.title.ilike(wildcard),
                    Book.author.ilike(wildcard),
                    Book.isbn.ilike(wildcard),
                )
            )
            .order_by(Book.title)
            .all()
        )

    @classmethod
    def create(cls, data: Dict[str, Any]) -> tuple[Book, Optional[str]]:
        """
        Add a new book to the catalogue.

        Business rules:
          - ISBN must be in a valid ISBN-10 or ISBN-13 format
          - ISBN must be unique across all books
          - Published year (if provided) must be between 1450 and the current year

        Returns:
            Tuple of (Book, error_message).  error_message is None on success.
        """
        # Validate ISBN format
        isbn = data.get("isbn", "")
        if not validate_isbn(isbn):
            return None, f"Invalid ISBN format: '{isbn}'"

        # Enforce ISBN uniqueness
        if Book.query.filter_by(isbn=isbn).first():
            return None, f"A book with ISBN '{isbn}' already exists"

        # Validate published year if provided
        year = data.get("published_year")
        if year is not None and not validate_year(int(year)):
            return None, f"Published year {year} is out of the valid range (1450 – present)"

        book = Book(
            title=data["title"],
            author=data["author"],
            isbn=isbn,
            genre=data.get("genre"),
            published_year=year,
        )
        db.session.add(book)
        db.session.commit()
        return book, None

    @classmethod
    def update(cls, book_id: int, data: Dict[str, Any]) -> tuple[Optional[Book], Optional[str]]:
        """
        Update mutable fields of an existing book.

        ISBN cannot be changed once set (it is the catalogue's natural key).

        Returns:
            Tuple of (Book, error_message).  error_message is None on success.
        """
        book = cls.get_by_id(book_id)
        if not book:
            return None, f"Book with id {book_id} not found"

        # Update only the fields that were provided
        if "title" in data:
            book.title = data["title"]
        if "author" in data:
            book.author = data["author"]
        if "genre" in data:
            book.genre = data["genre"]
        if "published_year" in data:
            year = int(data["published_year"])
            if not validate_year(year):
                return None, f"Published year {year} is out of the valid range"
            book.published_year = year

        db.session.commit()
        return book, None

    @classmethod
    def delete(cls, book_id: int) -> Optional[str]:
        """
        Remove a book from the catalogue.

        Business rule: a book that is currently on loan cannot be deleted.

        Returns:
            None on success, or an error message string on failure.
        """
        book = cls.get_by_id(book_id)
        if not book:
            return f"Book with id {book_id} not found"

        # Prevent deletion of checked-out books
        if not book.is_available:
            return f"Cannot delete '{book.title}' — it is currently on loan"

        db.session.delete(book)
        db.session.commit()
        return None
