import base64
import sys

import cv2
import numpy as np

from src.ocr import pdf_to_images

FIELD_NAMES = {
    1: "seller_name",
    2: "vat_number",
    3: "timestamp",
    4: "total",
    5: "vat_amount",
}


def find_qr_text(path):
    detector = cv2.QRCodeDetector()
    for img in pdf_to_images(path, dpi=200):
        arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        text, _, _ = detector.detectAndDecode(arr)
        if text:
            return text
    return None


def decode_tlv(qr_text):
    raw = base64.b64decode(qr_text)
    fields = {}
    i = 0
    while i < len(raw):
        tag = raw[i]
        length = raw[i + 1]
        value = raw[i + 2 : i + 2 + length].decode("utf-8")
        fields[FIELD_NAMES.get(tag, f"tag_{tag}")] = value
        i += 2 + length
    return fields


def read_qr(path):
    text = find_qr_text(path)
    if text is None:
        return None
    try:
        return decode_tlv(text)
    except Exception:
        return None


if __name__ == "__main__":
    result = read_qr(sys.argv[1])
    if result is None:
        print("No valid ZATCA QR code found")
    else:
        for name, value in result.items():
            print(f"{name:12} {value}")