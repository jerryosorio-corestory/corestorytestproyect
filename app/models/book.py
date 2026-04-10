"""
Book model — represents a physical book in the library catalogue.

Each book tracks its own availability so the system never double-lends it.
"""

from datetime import datetime
from app import db


class Book(db.Model):
    """SQLAlchemy ORM model for the 'books' table."""

    __tablename__ = "books"

    # Primary key — auto-incremented integer ID
    id = db.Column(db.Integer, primary_key=True)

    # Core catalogue fields
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    genre = db.Column(db.String(80), nullable=True)
    published_year = db.Column(db.Integer, nullable=True)

    # Availability flag — set to False when the book is checked out
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One book can have many loan records over its lifetime
    loans = db.relationship("Loan", back_populates="book", lazy="dynamic")

    def __repr__(self) -> str:
        status = "available" if self.is_available else "on loan"
        return f"<Book id={self.id} title='{self.title}' [{status}]>"
