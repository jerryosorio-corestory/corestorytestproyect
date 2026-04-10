"""
Loan API endpoints — mounted at /api/loans

Manages book checkout, return, and overdue tracking.

Endpoints:
  GET    /api/loans              — list all loan records
  POST   /api/loans              — check out a book (create a new loan)
  GET    /api/loans/overdue      — list all overdue loans
  GET    /api/loans/<id>         — get a single loan record
  POST   /api/loans/<id>/return  — return a book (close the loan)
  GET    /api/loans/<id>/fee     — preview the current late fee for a loan
"""

from flask import Blueprint, request, jsonify
from app.services.loan_service import LoanService

loans_bp = Blueprint("loans", __name__)


@loans_bp.route("", methods=["GET"])
def list_loans():
    """
    GET /api/loans
    Returns all loan records, most recent first.
    """
    loans = LoanService.get_all()
    result = [_loan_to_dict(loan) for loan in loans]
    return jsonify({"loans": result, "total": len(result)}), 200


@loans_bp.route("/overdue", methods=["GET"])
def list_overdue():
    """
    GET /api/loans/overdue
    Returns all open loans where the due date has passed.
    Ordered by due date ascending (oldest overdue first).
    """
    loans = LoanService.get_overdue()
    result = [_loan_to_dict(loan) for loan in loans]
    return jsonify({"overdue_loans": result, "total": len(result)}), 200


@loans_bp.route("/<int:loan_id>", methods=["GET"])
def get_loan(loan_id: int):
    """
    GET /api/loans/<loan_id>
    Retrieve a single loan record by ID.

    Path params:
      loan_id — integer primary key of the loan
    """
    loan = LoanService.get_by_id(loan_id)
    if not loan:
        return jsonify({"error": f"Loan with id {loan_id} not found"}), 404

    return jsonify(_loan_to_dict(loan)), 200


@loans_bp.route("", methods=["POST"])
def checkout():
    """
    POST /api/loans
    Check out a book to a member (creates a new loan record).

    Business rules enforced by LoanService:
      - Member must be ACTIVE
      - Member must be below the concurrent loan limit
      - Book must be available

    Request body (JSON):
      member_id (required) — ID of the borrowing member
      book_id   (required) — ID of the book to borrow
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    for field in ("member_id", "book_id"):
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400

    loan, error = LoanService.checkout(
        member_id=int(data["member_id"]),
        book_id=int(data["book_id"]),
    )
    if error:
        status = 404 if "not found" in error else 422
        return jsonify({"error": error}), status

    return jsonify(_loan_to_dict(loan)), 201


@loans_bp.route("/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id: int):
    """
    POST /api/loans/<loan_id>/return
    Record the return of a borrowed book and close the loan.

    Calculates and applies a late fee if the book is returned past the due date.
    The late fee is added to the member's outstanding balance.

    Path params:
      loan_id — integer primary key of the loan to close
    """
    loan, error = LoanService.return_book(loan_id)
    if error:
        status = 404 if "not found" in error else 422
        return jsonify({"error": error}), status

    response = _loan_to_dict(loan)
    if loan.late_fee > 0:
        response["message"] = (
            f"Book returned late. A fee of ${loan.late_fee:.2f} has been charged."
        )
    else:
        response["message"] = "Book returned on time. No fee charged."

    return jsonify(response), 200


@loans_bp.route("/<int:loan_id>/fee", methods=["GET"])
def preview_fee(loan_id: int):
    """
    GET /api/loans/<loan_id>/fee
    Preview the late fee that would be charged if the book were returned now.

    This is a read-only endpoint — it does not modify any data.
    Useful for staff to inform members of their current liability before return.
    """
    fee_info = LoanService.calculate_potential_fee(loan_id)
    return jsonify(fee_info), 200


def _loan_to_dict(loan) -> dict:
    """Convert a Loan ORM object to a JSON-serialisable dictionary."""
    return {
        "id": loan.id,
        "member_id": loan.member_id,
        "member_name": loan.member.full_name if loan.member else None,
        "book_id": loan.book_id,
        "book_title": loan.book.title if loan.book else None,
        "checkout_date": loan.checkout_date.isoformat(),
        "due_date": loan.due_date.isoformat(),
        "returned": loan.returned,
        "return_date": loan.return_date.isoformat() if loan.return_date else None,
        "late_fee": round(loan.late_fee, 2),
        "is_overdue": loan.is_overdue,
        "days_overdue": loan.days_overdue,
    }
