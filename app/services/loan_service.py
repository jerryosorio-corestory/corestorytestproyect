"""
LoanService — the core business logic engine for borrowing and returning books.

This service enforces all library policies:
  - Member must be ACTIVE to borrow
  - Member must not exceed the concurrent loan limit
  - Book must be available (not already checked out)
  - Late fees are calculated when a book is returned past its due date
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from flask import current_app
from app import db
from app.models.loan import Loan
from app.models.book import Book
from app.models.member import Member, MemberStatus
from app.services.member_service import MemberService


class LoanService:
    """Stateless service class for checkout/return operations."""

    @classmethod
    def get_all(cls) -> List[Loan]:
        """Return all loan records, most recent first."""
        return Loan.query.order_by(Loan.checkout_date.desc()).all()

    @classmethod
    def get_by_id(cls, loan_id: int) -> Optional[Loan]:
        """Fetch a single loan by primary key; returns None if not found."""
        return Loan.query.get(loan_id)

    @classmethod
    def get_overdue(cls) -> List[Loan]:
        """Return all loans that are past their due date and not yet returned."""
        now = datetime.utcnow()
        return (
            Loan.query.filter(
                Loan.returned == False,
                Loan.due_date < now,
            )
            .order_by(Loan.due_date)
            .all()
        )

    @classmethod
    def get_member_loans(cls, member_id: int) -> List[Loan]:
        """Return all loans for a specific member, most recent first."""
        return (
            Loan.query.filter_by(member_id=member_id)
            .order_by(Loan.checkout_date.desc())
            .all()
        )

    @classmethod
    def checkout(cls, member_id: int, book_id: int) -> tuple[Optional[Loan], Optional[str]]:
        """
        Check out a book to a member.

        Business rules enforced:
          1. Member must exist and be in ACTIVE status
          2. Member must not already have MAX_LOANS_PER_MEMBER open loans
          3. Book must exist and be available (is_available == True)

        On success:
          - Creates a Loan record with a due_date = today + LOAN_PERIOD_DAYS
          - Sets book.is_available = False

        Returns:
            Tuple of (Loan, error_message).  error_message is None on success.
        """
        # --- Rule 1: Validate member ---
        member = Member.query.get(member_id)
        if not member:
            return None, f"Member with id {member_id} not found"

        if member.status != MemberStatus.ACTIVE:
            return None, (
                f"Member '{member.full_name}' cannot borrow books — "
                f"account status is '{member.status}'"
            )

        # --- Rule 2: Enforce concurrent loan limit ---
        max_loans = current_app.config["MAX_LOANS_PER_MEMBER"]
        if member.active_loans_count >= max_loans:
            return None, (
                f"Member '{member.full_name}' already has {max_loans} books on loan. "
                f"Return a book before borrowing another."
            )

        # --- Rule 3: Validate book availability ---
        book = Book.query.get(book_id)
        if not book:
            return None, f"Book with id {book_id} not found"

        if not book.is_available:
            return None, f"'{book.title}' is not available — it is currently on loan"

        # --- Create loan record ---
        loan_period = current_app.config["LOAN_PERIOD_DAYS"]
        loan = Loan(
            member_id=member_id,
            book_id=book_id,
            checkout_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=loan_period),
        )

        # Mark the book as unavailable
        book.is_available = False

        db.session.add(loan)
        db.session.commit()
        return loan, None

    @classmethod
    def return_book(cls, loan_id: int) -> tuple[Optional[Loan], Optional[str]]:
        """
        Process the return of a borrowed book.

        Business rules:
          - Loan must exist and must not already be closed
          - If returned late, calculate late_fee = days_overdue * LATE_FEE_PER_DAY
            capped at MAX_LATE_FEE
          - Add any late fee to the member's outstanding balance
          - Set book.is_available = True so it can be borrowed again

        Returns:
            Tuple of (Loan, error_message).  error_message is None on success.
        """
        loan = cls.get_by_id(loan_id)
        if not loan:
            return None, f"Loan with id {loan_id} not found"

        if loan.returned:
            return None, f"Loan {loan_id} has already been closed (book was previously returned)"

        # Record return timestamp
        loan.return_date = datetime.utcnow()
        loan.returned = True

        # --- Late fee calculation ---
        if loan.is_overdue:
            fee_per_day = current_app.config["LATE_FEE_PER_DAY"]
            max_fee = current_app.config["MAX_LATE_FEE"]
            raw_fee = loan.days_overdue * fee_per_day
            loan.late_fee = min(raw_fee, max_fee)  # Cap the fee at the configured maximum

            # Charge the fee to the member's account
            MemberService.apply_late_fee(loan.member_id, loan.late_fee)

        # Restore book availability
        loan.book.is_available = True

        db.session.commit()
        return loan, None

    @classmethod
    def calculate_potential_fee(cls, loan_id: int) -> Dict[str, Any]:
        """
        Calculate what the late fee would be if the book were returned right now.

        Used by the UI to show members how much they owe before they physically
        return the book. Does NOT modify any database record.

        Returns:
            Dict with 'days_overdue', 'fee_per_day', 'potential_fee', and 'is_overdue'.
        """
        loan = cls.get_by_id(loan_id)
        if not loan or loan.returned:
            return {"days_overdue": 0, "potential_fee": 0.0, "is_overdue": False}

        fee_per_day = current_app.config["LATE_FEE_PER_DAY"]
        max_fee = current_app.config["MAX_LATE_FEE"]
        days = loan.days_overdue
        raw_fee = days * fee_per_day

        return {
            "is_overdue": loan.is_overdue,
            "days_overdue": days,
            "fee_per_day": fee_per_day,
            "potential_fee": min(raw_fee, max_fee),
        }
