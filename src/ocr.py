import sys

import pymupdf
import pytesseract
from PIL import Image


def pdf_to_images(path, dpi=200):
    doc = pymupdf.open(path)
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(img)
    doc.close()
    return images


def ocr_pdf(path):
    text = ""
    for img in pdf_to_images(path):
        text += pytesseract.image_to_string(img, lang="eng+ara")
    return text


if __name__ == "__main__":
    print(ocr_pdf(sys.argv[1]))