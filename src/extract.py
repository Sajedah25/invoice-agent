import sys

from src.llm import generate_json
from src.read_invoice import read_invoice
from src.schema import Invoice

PROMPT = """You are an accounts payable assistant. Extract the invoice fields from the text below.

Rules:
- Use only information that appears in the text. Do not guess.
- Dates must be in YYYY-MM-DD format.
- Amounts must be plain numbers without commas or currency, for example 1460.50.
- The supplier is the company that issued the invoice, not the "Bill To" company.

Invoice text:
---
{text}
---
"""


def extract_invoice(text):
    raw_json = generate_json(PROMPT.format(text=text), Invoice)
    return Invoice.model_validate_json(raw_json)


if __name__ == "__main__":
    result = read_invoice(sys.argv[1])
    print(f"Read method: {result['method']}\n")
    invoice = extract_invoice(result["text"])
    print(invoice.model_dump_json(indent=2))