"""Invoice extraction tool + semantic validator for chapter 6.1.

INVOICE_TOOL is the Claude tool-use schema you force with tool_choice — its
input_schema IS the output shape. validate_invoice checks the *values* (the
semantics a JSON schema cannot express): that line items actually sum to the
stated total, and that required fields are present. It returns a list of
human-readable error strings; an empty list means the extraction is valid.
"""

INVOICE_TOOL = {
    "name": "record_invoice",
    "description": "Record the structured fields extracted from an invoice document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "The billing party / supplier name."},
            "total": {"type": "number", "description": "The invoice's stated grand total."},
            "line_items": {
                "type": "array",
                "description": "Each charge on the invoice.",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["description", "amount"],
                },
            },
            # Nullable on purpose: many invoices omit a due date. Marking it
            # required would pressure the model to fabricate one (see 6.1 lesson).
            "due_date": {"type": ["string", "null"], "description": "ISO date, or null if absent."},
        },
        "required": ["vendor", "total", "line_items"],
    },
}


def validate_invoice(data: dict) -> list[str]:
    """Semantic validation the JSON schema cannot enforce.

    Returns a list of specific error strings (empty == valid). These strings are
    what your retry loop feeds back to the model so it can self-correct.
    """
    errors: list[str] = []

    for field in ("vendor", "total", "line_items"):
        if data.get(field) in (None, "", []):
            errors.append(f"missing required field: {field}")

    items = data.get("line_items") or []
    try:
        calculated_total = round(sum(item["amount"] for item in items), 2)
    except (KeyError, TypeError):
        errors.append("every line_item needs a numeric 'amount'")
        return errors

    stated_total = data.get("total")
    if stated_total is not None and items and calculated_total != stated_total:
        errors.append(
            f"line_items sum to {calculated_total} but stated total is {stated_total}"
        )

    return errors


# A sample document you can use when running against the real API (see __main__
# in extraction_loop.py). The stated total here is deliberately consistent.
SAMPLE_INVOICE = """
INVOICE — Acme Supply Co.
  Widgets ........ $100.00
  Gaskets ........  $50.00
  TOTAL .......... $150.00
""".strip()
