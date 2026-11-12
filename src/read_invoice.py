import sys

from src.ocr import ocr_pdf
from src.read_pdf import is_scanned, read_pdf_text


def read_invoice(path):
    text = read_pdf_text(path)
    if not is_scanned(text):
        return {"text": text, "method": "digital"}
    return {"text": ocr_pdf(path), "method": "ocr"}


if __name__ == "__main__":
    result = read_invoice(sys.argv[1])
    print(f"Method: {result['method']}")
    print(f"Characters read: {len(result['text'])}")
    print("-" * 40)
    print(result["text"])