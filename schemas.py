# schemas.py
from pydantic import BaseModel, Field
from datetime import date

class InvoiceCreate(BaseModel):
    client_name: str = Field(..., example="Clínica XYZ")
    client_id: str = Field(..., example="900123456-7")
    invoice_number: str = Field(..., example="CC-2025-0001")
    issue_date: date = Field(..., example="2025-12-09")
    amount: float = Field(..., example=2500000)
    concept: str = Field(..., example="Servicios profesionales anestesiología noviembre 2025")


class InvoiceResponse(BaseModel):
    invoice_id: str
    pdf_file_id: str
