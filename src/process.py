import sys

from pydantic import ValidationError

from src.extract import extract_invoice
from src.llm import LLMUnavailable
from src.qr import read_qr
from src.read_invoice import read_invoice
from src.validate import decide, validate_invoice


def process_file(path, seen):
    text = read_invoice(path)
    try:
        invoice = extract_invoice(text["text"])
    except LLMUnavailable:
        print("Decision:    PENDING (AI unavailable, will retry later)")
        return
    except ValidationError as e:
        print("Decision:    NEEDS REVIEW (AI could not read the invoice correctly)")
        print(f"  {e.error_count()} field error(s), a person must fill them in")
        return

    qr = read_qr(path)
    results = validate_invoice(invoice, qr, seen)
    seen.add((invoice.supplier_vat_number, invoice.invoice_number))

    print(f"Read method: {text['method']}")
    print(f"Decision:    {decide(results).upper()}")
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"  [{mark}] {r.name:11} {r.message}")


def process_files(paths):
    seen = set()
    for path in paths:
        print(f"\n=== {path}")
        process_file(path, seen)


if __name__ == "__main__":
    process_files(sys.argv[1:])