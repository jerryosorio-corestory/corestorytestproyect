"""
MemberService — business logic for managing library members.

Responsibilities:
  - Register new members with validated data
  - Update member information and status
  - Suspend or reactivate members based on fee thresholds
  - Enforce email uniqueness
"""

from typing import List, Optional, Dict, Any
from app import db
from app.models.member import Member, MemberStatus
from app.utils.validators import validate_email

# Outstanding fee threshold (USD) at which a member is automatically suspended
AUTO_SUSPEND_FEE_THRESHOLD = 5.00


class MemberService:
    """Stateless service class for member-related operations."""

    @classmethod
    def get_all(cls) -> List[Member]:
        """Return all members ordered by last name, then first name."""
        return Member.query.order_by(Member.last_name, Member.first_name).all()

    @classmethod
    def get_by_id(cls, member_id: int) -> Optional[Member]:
        """Fetch a single member by primary key; returns None if not found."""
        return Member.query.get(member_id)

    @classmethod
    def get_by_email(cls, email: str) -> Optional[Member]:
        """Fetch a member by their unique email address."""
        return Member.query.filter_by(email=email.lower()).first()

    @classmethod
    def register(cls, data: Dict[str, Any]) -> tuple[Optional[Member], Optional[str]]:
        """
        Register a new library member.

        Business rules:
          - Email must be in a valid format
          - Email must be unique in the system
          - First and last name are required

        Returns:
            Tuple of (Member, error_message).  error_message is None on success.
        """
        email = data.get("email", "").strip().lower()

        # Validate email format
        if not validate_email(email):
            return None, f"Invalid email address: '{email}'"

        # Enforce email uniqueness
        if cls.get_by_email(email):
            return None, f"A member with email '{email}' already exists"

        member = Member(
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            email=email,
            phone=data.get("phone", "").strip() or None,
        )
        db.session.add(member)
        db.session.commit()
        return member, None

    @classmethod
    def update(cls, member_id: int, data: Dict[str, Any]) -> tuple[Optional[Member], Optional[str]]:
        """
        Update a member's personal information.

        Email cannot be changed to one already used by another member.

        Returns:
            Tuple of (Member, error_message).  error_message is None on success.
        """
        member = cls.get_by_id(member_id)
        if not member:
            return None, f"Member with id {member_id} not found"

        if "first_name" in data:
            member.first_name = data["first_name"].strip()
        if "last_name" in data:
            member.last_name = data["last_name"].strip()
        if "phone" in data:
            member.phone = data["phone"].strip() or None

        if "email" in data:
            new_email = data["email"].strip().lower()
            if not validate_email(new_email):
                return None, f"Invalid email address: '{new_email}'"
            existing = cls.get_by_email(new_email)
            if existing and existing.id != member_id:
                return None, f"Email '{new_email}' is already registered to another member"
            member.email = new_email

        db.session.commit()
        return member, None

    @classmethod
    def apply_late_fee(cls, member_id: int, amount: float) -> tuple[Optional[Member], Optional[str]]:
        """
        Add a late fee to a member's outstanding balance.

        Business rule: if outstanding fees exceed AUTO_SUSPEND_FEE_THRESHOLD,
        the member's status is automatically set to SUSPENDED.

        Returns:
            Tuple of (Member, error_message).  error_message is None on success.
        """
        member = cls.get_by_id(member_id)
        if not member:
            return None, f"Member with id {member_id} not found"

        member.outstanding_fees += amount

        # Automatically suspend members who accumulate excessive fees
        if member.outstanding_fees >= AUTO_SUSPEND_FEE_THRESHOLD:
            member.status = MemberStatus.SUSPENDED

        db.session.commit()
        return member, None

    @classmethod
    def pay_fees(cls, member_id: int, amount: float) -> tuple[Optional[Member], Optional[str]]:
        """
        Record a fee payment and, if balance is cleared, reactivate the member.

        Business rule: paying off all outstanding fees resets status to ACTIVE.

        Returns:
            Tuple of (Member, error_message).  error_message is None on success.
        """
        member = cls.get_by_id(member_id)
        if not member:
            return None, f"Member with id {member_id} not found"

        if amount <= 0:
            return None, "Payment amount must be greater than zero"

        # Clamp the balance at zero — overpayment is not refunded
        member.outstanding_fees = max(0.0, member.outstanding_fees - amount)

        # Reinstate borrowing privileges once the balance is cleared
        if member.outstanding_fees == 0.0 and member.status == MemberStatus.SUSPENDED:
            member.status = MemberStatus.ACTIVE

        db.session.commit()
        return member, None
