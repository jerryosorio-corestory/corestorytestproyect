"""
Loan model — represents a single checkout transaction linking a Member to a Book.

A loan is open when returned=False and closed once the book is handed back.
Late fees accumulate for each day the book is kept beyond the due date.
"""

from datetime import datetime, timedelta
from app import db


class Loan(db.Model):
    """SQLAlchemy ORM model for the 'loans' table."""

    __tablename__ = "loans"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys that link the loan to its member and book
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)

    # Checkout and due dates
    checkout_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)

    # Return tracking — set when the book is physically returned
    returned = db.Column(db.Boolean, default=False, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)

    # Late fee charged for this specific loan (USD)
    late_fee = db.Column(db.Float, default=0.0, nullable=False)

    # Relationships back to parent models
    member = db.relationship("Member", back_populates="loans")
    book = db.relationship("Book", back_populates="loans")

    @property
    def is_overdue(self) -> bool:
        """Return True if the loan is still open and past its due date."""
        if self.returned:
            return False
        return datetime.utcnow() > self.due_date

    @property
    def days_overdue(self) -> int:
        """Number of full days past the due date (0 if not overdue)."""
        if not self.is_overdue:
            return 0
        delta = datetime.utcnow() - self.due_date
        return delta.days

    def __repr__(self) -> str:
        status = "returned" if self.returned else ("OVERDUE" if self.is_overdue else "open")
        return f"<Loan id={self.id} member={self.member_id} book={self.book_id} [{status}]>"
