import sys

import pymupdf


def read_pdf_text(path):
    doc = pymupdf.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def is_scanned(text):
    return len(text.strip()) < 20


if __name__ == "__main__":
    path = sys.argv[1]
    text = read_pdf_text(path)
    if is_scanned(text):
        print(f"{path}: SCANNED (no text found) -> needs OCR")
    else:
        print(f"{path}: DIGITAL (text found)\n")
        print(text)