from pydantic import ValidationError

from src.schema import Invoice

sample = {
    "supplier_name": "Sample Supplies Co.",
    "supplier_vat_number": "300000000000003",
    "invoice_number": "INV-2026-0042",
    "issue_date": "2026-11-10",
    "due_date": "2026-12-10",
    "subtotal": "1270.00",
    "vat_amount": "190.50",
    "total": "1460.50",
    "items": [
        {"description": "A4 paper (box)", "quantity": 20, "unit_price": "25.00", "line_total": "500.00"},
        {"description": "Printer toner", "quantity": 4, "unit_price": "180.00", "line_total": "720.00"},
        {"description": "Delivery", "quantity": 1, "unit_price": "50.00", "line_total": "50.00"},
    ],
}

invoice = Invoice(**sample)
print("Valid invoice:")
print(invoice.model_dump_json(indent=2))

broken = dict(sample, total="one thousand", issue_date="next week")
try:
    Invoice(**broken)
except ValidationError as e:
    print("\nBroken invoice rejected:")
    print(e)