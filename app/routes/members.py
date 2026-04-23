"""
Member API endpoints — mounted at /api/members

Handles member registration, profile updates, and fee management.

Endpoints:
  GET    /api/members              — list all members
  POST   /api/members              — register a new member
  GET    /api/members/<id>         — get a member's profile
  PUT    /api/members/<id>         — update member information
  POST   /api/members/<id>/pay     — record a fee payment
  GET    /api/members/<id>/loans   — list all loans for a member
"""

from flask import Blueprint, request, jsonify
from app.services.member_service import MemberService
from app.services.loan_service import LoanService

members_bp = Blueprint("members", __name__)


@members_bp.route("", methods=["GET"])
def list_members():
    """
    GET /api/members
    Returns all registered members ordered by last name.

    Query params:
      status (optional) — filter by membership status: active | suspended | expired
    """
    status_filter = request.args.get("status")
    if status_filter:
        from app.models.member import MemberStatus
        if status_filter not in MemberStatus.ALL:
            return jsonify({"error": f"Invalid status '{status_filter}'. Must be one of: {MemberStatus.ALL}"}), 400
        members = MemberService.get_by_status(status_filter)
    else:
        members = MemberService.get_all()
    result = [_member_to_dict(m) for m in members]
    return jsonify({"members": result, "total": len(result)}), 200


@members_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id: int):
    """
    GET /api/members/<member_id>
    Retrieve a single member's profile by ID.

    Path params:
      member_id — integer primary key
    """
    member = MemberService.get_by_id(member_id)
    if not member:
        return jsonify({"error": f"Member with id {member_id} not found"}), 404

    return jsonify(_member_to_dict(member)), 200


@members_bp.route("", methods=["POST"])
def register_member():
    """
    POST /api/members
    Register a new library member.

    Request body (JSON):
      first_name (required)
      last_name  (required)
      email      (required) — must be unique and valid format
      phone      (optional)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    for field in ("first_name", "last_name", "email"):
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400

    member, error = MemberService.register(data)
    if error:
        return jsonify({"error": error}), 422

    return jsonify(_member_to_dict(member)), 201


@members_bp.route("/<int:member_id>", methods=["PUT"])
def update_member(member_id: int):
    """
    PUT /api/members/<member_id>
    Update a member's personal information.

    Request body (JSON) — all fields optional:
      first_name, last_name, email, phone
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    member, error = MemberService.update(member_id, data)
    if error:
        status = 404 if "not found" in error else 422
        return jsonify({"error": error}), status

    return jsonify(_member_to_dict(member)), 200


@members_bp.route("/<int:member_id>/pay", methods=["POST"])
def pay_fees(member_id: int):
    """
    POST /api/members/<member_id>/pay
    Record a payment toward a member's outstanding late fees.

    Request body (JSON):
      amount (required) — positive float, amount paid in USD
    """
    data = request.get_json()
    if not data or "amount" not in data:
        return jsonify({"error": "Field 'amount' is required"}), 400

    try:
        amount = float(data["amount"])
    except (ValueError, TypeError):
        return jsonify({"error": "'amount' must be a numeric value"}), 400

    member, error = MemberService.pay_fees(member_id, amount)
    if error:
        status = 404 if "not found" in error else 422
        return jsonify({"error": error}), status

    return jsonify({
        "message": f"Payment of ${amount:.2f} recorded",
        "member": _member_to_dict(member),
    }), 200


@members_bp.route("/<int:member_id>/loans", methods=["GET"])
def member_loans(member_id: int):
    """
    GET /api/members/<member_id>/loans
    List all loan history for a specific member.
    """
    member = MemberService.get_by_id(member_id)
    if not member:
        return jsonify({"error": f"Member with id {member_id} not found"}), 404

    loans = LoanService.get_member_loans(member_id)
    result = [_loan_to_dict(loan) for loan in loans]
    return jsonify({"loans": result, "total": len(result)}), 200


def _member_to_dict(member) -> dict:
    """Convert a Member ORM object to a JSON-serialisable dictionary."""
    return {
        "id": member.id,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "full_name": member.full_name,
        "email": member.email,
        "phone": member.phone,
        "status": member.status,
        "outstanding_fees": round(member.outstanding_fees, 2),
        "active_loans_count": member.active_loans_count,
        "created_at": member.created_at.isoformat() if member.created_at else None,
    }


def _loan_to_dict(loan) -> dict:
    """Minimal loan representation used inside member responses."""
    return {
        "id": loan.id,
        "book_id": loan.book_id,
        "book_title": loan.book.title if loan.book else None,
        "checkout_date": loan.checkout_date.isoformat(),
        "due_date": loan.due_date.isoformat(),
        "returned": loan.returned,
        "return_date": loan.return_date.isoformat() if loan.return_date else None,
        "late_fee": loan.late_fee,
        "is_overdue": loan.is_overdue,
    }
