import sys

from pydantic import ValidationError

from src import db
from src.extract import extract_invoice
from src.llm import LLMUnavailable
from src.qr import read_qr
from src.read_invoice import read_invoice
from src.validate import decide, validate_invoice


def process_file(path):
    text = read_invoice(path)
    try:
        invoice = extract_invoice(text["text"])
    except LLMUnavailable:
        invoice_id = db.save_unread(path, text["method"], "pending", "AI unavailable, retry later")
        print(f"#{invoice_id} PENDING (AI unavailable, will retry later)")
        return
    except ValidationError as e:
        invoice_id = db.save_unread(path, text["method"], "needs_review", f"{e.error_count()} field error(s)")
        print(f"#{invoice_id} NEEDS REVIEW (AI could not read the invoice correctly)")
        return

    qr = read_qr(path)
    exists = db.is_duplicate(invoice.supplier_vat_number, invoice.invoice_number)
    results = validate_invoice(invoice, qr, exists)
    status = decide(results)
    invoice_id = db.save_invoice(invoice, path, text["method"], status, results)

    print(f"#{invoice_id} {status.upper()}  (read: {text['method']})")
    for r in results:
        if not r.passed:
            print(f"   FAIL {r.name}: {r.message}")


def process_files(paths):
    db.init_db()
    for path in paths:
        print(f"\n=== {path}")
        process_file(path)


if __name__ == "__main__":
    process_files(sys.argv[1:])