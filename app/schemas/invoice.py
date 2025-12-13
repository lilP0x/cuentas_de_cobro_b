# app/schemas/invoice.py
"""
Schemas de Pydantic para validación de datos de entrada/salida de la API.
Define qué datos recibe y retorna cada endpoint.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class InvoiceBase(BaseModel):
    """Campos base compartidos por todos los schemas de factura."""
    invoice_number: str = Field(..., description="Número de la factura", min_length=1)
    client_name: str = Field(..., description="Nombre del cliente", min_length=1)
    client_id: str = Field(..., description="NIT o documento del cliente", min_length=1)
    concept: str = Field(..., description="Concepto o descripción del servicio/producto")
    amount: float = Field(..., gt=0, description="Monto total de la factura")
    issue_date: date = Field(default_factory=date.today, description="Fecha de emisión")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Valida que el monto sea positivo."""
        if v <= 0:
            raise ValueError('El monto debe ser mayor a 0')
        return round(v, 2)


class InvoiceCreate(InvoiceBase):
    """Schema para crear una nueva factura."""
    @validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("El valor debe ser positivo")
        return v


class InvoiceUpdate(BaseModel):
    """Schema para actualizar una factura existente.
    
    Todos los campos son opcionales para permitir actualización parcial.
    """
    invoice_number: Optional[str] = Field(None, min_length=1)
    client_name: Optional[str] = Field(None, min_length=1)
    client_id: Optional[str] = Field(None, min_length=1)
    concept: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    issue_date: Optional[date] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El monto debe ser mayor a 0')
        return round(v, 2) if v else v


class InvoiceResponse(InvoiceBase):
    """Schema de respuesta que retorna la API.
    
    Incluye campos adicionales como id y created_at que genera el servidor.
    """
    id: str = Field(..., description="ID único de la factura")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    pdf_url: Optional[str] = Field(None, description="URL para descargar el PDF")
    
    class Config:
        """Configuración de Pydantic."""
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "invoice_number": "FC-001",
                "client_name": "Juan Pérez",
                "client_id": "1234567890",
                "concept": "Servicios de desarrollo web - Noviembre 2025",
                "amount": 1500000.00,
                "issue_date": "2025-12-13",
                "created_at": "2025-12-13T10:30:00",
                "pdf_url": "/invoices/507f1f77bcf86cd799439011/pdf"
            }
        }


class InvoiceListResponse(BaseModel):
    """Schema para listar múltiples facturas con paginación."""
    total: int = Field(..., description="Total de facturas")
    page: int = Field(1, ge=1, description="Página actual")
    page_size: int = Field(10, ge=1, le=100, description="Elementos por página")
    invoices: List[InvoiceResponse] = Field(default_factory=list, description="Lista de facturas")
