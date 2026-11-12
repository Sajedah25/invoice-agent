from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal


class Invoice(BaseModel):
    supplier_name: str
    supplier_vat_number: str
    invoice_number: str
    issue_date: date
    due_date: date | None = None
    subtotal: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str = "SAR"
    items: list[LineItem] = []