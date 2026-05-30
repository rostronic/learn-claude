"""Dummy workflow steps for chapter 4.1 — a support-refund workflow.

These stand in for real tools an agent would call. Each returns a fixed
payload. Your gate (in workflow.py) decides *whether* a step is allowed to
run; these functions are what runs once it is.
"""


def verify_identity(customer_id: str) -> dict:
    """Pretend to verify the customer's identity. Always succeeds here."""
    return {"customer_id": customer_id, "verified": True}


def check_refund_policy(order_id: str, amount: float) -> dict:
    """Pretend to evaluate the refund policy for an order.

    Returns an eligibility decision. The gate keys off `eligible`.
    Orders over $500 are deemed ineligible for an automatic refund.
    """
    return {"order_id": order_id, "amount": amount, "eligible": amount <= 500}


def issue_refund(order_id: str, amount: float) -> dict:
    """The guarded action: actually move money. Must not run until its
    prerequisites (identity + policy) are satisfied."""
    return {"order_id": order_id, "amount": amount, "refunded": True}
