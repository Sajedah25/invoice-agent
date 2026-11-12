from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.schema import Invoice

VAT_RATE = Decimal("0.15")
TOLERANCE = Decimal("0.01")


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


def close_enough(a, b):
    return abs(Decimal(a) - Decimal(b)) <= TOLERANCE


def check_vat_number(inv):
    v = inv.supplier_vat_number
    ok = len(v) == 15 and v.isdigit() and v.startswith("3") and v.endswith("3")
    msg = "VAT number format is valid" if ok else f"VAT number '{v}' must be 15 digits, starting and ending with 3"
    return CheckResult("vat_number", ok, msg)


def check_vat_math(inv):
    expected = (inv.subtotal * VAT_RATE).quantize(Decimal("0.01"))
    ok = close_enough(inv.vat_amount, expected)
    msg = "VAT is 15% of subtotal" if ok else f"VAT should be {expected} but invoice shows {inv.vat_amount}"
    return CheckResult("vat_math", ok, msg)


def check_total(inv):
    expected = inv.subtotal + inv.vat_amount
    ok = close_enough(inv.total, expected)
    msg = "Subtotal + VAT = total" if ok else f"Total should be {expected} but invoice shows {inv.total}"
    return CheckResult("total", ok, msg)


def check_line_items(inv):
    if not inv.items:
        return CheckResult("line_items", True, "No line items to check")
    for item in inv.items:
        if not close_enough(item.quantity * item.unit_price, item.line_total):
            return CheckResult("line_items", False, f"Line '{item.description}': {item.quantity} x {item.unit_price} is not {item.line_total}")
    items_sum = sum(item.line_total for item in inv.items)
    ok = close_enough(items_sum, inv.subtotal)
    msg = "Line items add up to subtotal" if ok else f"Line items add up to {items_sum} but subtotal is {inv.subtotal}"
    return CheckResult("line_items", ok, msg)


def check_dates(inv):
    if inv.issue_date > date.today():
        return CheckResult("dates", False, f"Issue date {inv.issue_date} is in the future")
    if inv.due_date and inv.due_date < inv.issue_date:
        return CheckResult("dates", False, "Due date is before issue date")
    return CheckResult("dates", True, "Dates make sense")


def check_qr(inv, qr):
    if qr is None:
        return CheckResult("qr", False, "No valid ZATCA QR code found")
    problems = []
    if qr.get("vat_number") != inv.supplier_vat_number:
        problems.append(f"VAT number (QR {qr.get('vat_number')} vs invoice {inv.supplier_vat_number})")
    if not close_enough(qr.get("total", "0"), inv.total):
        problems.append(f"total (QR {qr.get('total')} vs invoice {inv.total})")
    if not close_enough(qr.get("vat_amount", "0"), inv.vat_amount):
        problems.append(f"VAT (QR {qr.get('vat_amount')} vs invoice {inv.vat_amount})")
    if qr.get("timestamp", "")[:10] != inv.issue_date.isoformat():
        problems.append(f"date (QR {qr.get('timestamp', '')[:10]} vs invoice {inv.issue_date})")
    if problems:
        return CheckResult("qr", False, "QR does not match: " + "; ".join(problems))
    return CheckResult("qr", True, "QR matches the invoice")


def check_duplicate(inv, seen):
    key = (inv.supplier_vat_number, inv.invoice_number)
    if key in seen:
        return CheckResult("duplicate", False, f"Duplicate: invoice {inv.invoice_number} from this supplier was already processed")
    return CheckResult("duplicate", True, "Not a duplicate")


def validate_invoice(inv: Invoice, qr, seen):
    return [
        check_vat_number(inv),
        check_vat_math(inv),
        check_total(inv),
        check_line_items(inv),
        check_dates(inv),
        check_qr(inv, qr),
        check_duplicate(inv, seen),
    ]


def decide(results):
    return "approved" if all(r.passed for r in results) else "flagged"