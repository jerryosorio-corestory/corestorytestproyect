"""
Member model — represents a registered library member.

Members must be in ACTIVE status to borrow books.
A SUSPENDED member has unpaid fees or policy violations.
"""

from datetime import datetime, timezone
from app import db


class MemberStatus:
    """Enumeration of valid member statuses (kept as plain strings for SQLite compatibility)."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

    ALL = [ACTIVE, SUSPENDED, EXPIRED]


class Member(db.Model):
    """SQLAlchemy ORM model for the 'members' table."""

    __tablename__ = "members"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Personal information
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    # Membership status — controls borrowing privileges
    status = db.Column(db.String(20), default=MemberStatus.ACTIVE, nullable=False)

    # Accumulated unpaid late fees in USD
    outstanding_fees = db.Column(db.Float, default=0.0, nullable=False)

    # Audit timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # A member can have many loans over time
    loans = db.relationship("Loan", back_populates="member", lazy="dynamic")

    @property
    def full_name(self) -> str:
        """Convenience property returning the member's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def active_loans_count(self) -> int:
        """Count of loans that have not yet been returned."""
        return self.loans.filter_by(returned=False).count()

    def __repr__(self) -> str:
        return f"<Member id={self.id} name='{self.full_name}' status='{self.status}'>"
