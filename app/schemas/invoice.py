from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import List, Optional, Literal
from typing import Literal

PaymentTermsType = Literal["CASH", "CREDIT"]  # contado vs crédito
ClientType = Literal["COMPANY", "PERSON"]


class InvoiceItem(BaseModel):
    description: str = Field(..., min_length=1, example="Cafe 340 gr")
    quantity: float = Field(..., gt=0, example=1)
    unit: str = Field("und", min_length=1, example="und")
    unit_price: int = Field(..., ge=0, example=170000)

    @property
    def subtotal(self) -> int:
        return int(round(self.quantity * self.unit_price))

ClientType = Literal["COMPANY", "PERSON"]

class InvoiceCreate(BaseModel):
    client_type: ClientType = Field(..., example="COMPANY")
    client_name: str = Field(..., min_length=1, example="EOBO CAFÉ")
    items: List[InvoiceItem] = Field(..., min_length=1)
    issue_date: date = Field(..., example="2025-12-15")
    payment_terms_type: PaymentTermsType = Field(..., example="CREDIT")
    credit_days: Optional[int] = Field(None, ge=0, le=365, example=20)
    due_date_override: Optional[date] = None



class InvoiceResponse(BaseModel):
    invoice_id: str
    invoice_number: int
    pdf_file_id: str
    total_amount: int
    total_amount_text: str
    due_date: Optional[date] = None
