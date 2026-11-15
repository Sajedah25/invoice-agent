import shutil
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from src import db
from src.agent import agent

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
db.init_db()

app = FastAPI(title="Invoice Agent API")


class Review(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/invoices")
def upload_invoice(file: UploadFile = File(...)):
    name = Path(file.filename).name
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{name}"
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    state = agent.invoke({"path": str(path)})
    return db.get_invoice(state["invoice_id"])


@app.get("/invoices")
def list_all(status: str | None = None):
    return [dict(row) for row in db.list_invoices(status)]


@app.get("/invoices/{invoice_id}")
def get_one(invoice_id: int):
    invoice = db.get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@app.post("/invoices/{invoice_id}/review")
def review(invoice_id: int, review: Review):
    if not db.review_invoice(invoice_id, review.decision, review.note):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db.get_invoice(invoice_id)