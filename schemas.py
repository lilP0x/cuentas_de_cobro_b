# schemas.py
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


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


class ClientPdfItem(BaseModel):
    invoice_id: str
    invoice_number: str
    issue_date: date
    pdf_file_id: str
    amount: float
    concept: Optional[str]


class ClientPdfsResponse(BaseModel):
    client_id: str
    client_name: Optional[str]
    pdfs: List[ClientPdfItem]


class ClientCreate(BaseModel):
    client_id: str = Field(..., example="900123456-7")
    client_name: str = Field(..., example="Soluciones Creativas S.A.S.")
    contact_email: Optional[str] = Field(None, example="cliente@example.com")
    phone: Optional[str] = Field(None, example="+57 300 000 0000")
    address: Optional[str] = Field(None, example="Carrera 15 # 80 - 20")


class ClientResponse(BaseModel):
    client_id: str
    client_name: Optional[str]
    pdf_file_ids: Optional[List[str]] = []


class ClientUpdate(BaseModel):
    client_name: Optional[str]
    contact_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]


# ---------- Productos (Products) ----------
class ProductCreate(BaseModel):
    name: str = Field(..., example="Cafemundo Premium")
    price: float = Field(..., example=19900)
    stock: int = Field(..., example=100)


class ProductResponse(BaseModel):
    product_id: Optional[str]
    name: str
    price: float
    stock: int


class ProductUpdate(BaseModel):
    name: Optional[str]
    price: Optional[float]
    stock: Optional[int]