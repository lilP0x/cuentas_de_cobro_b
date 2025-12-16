from datetime import timedelta, date
from typing import Optional
from app.schemas.invoice import InvoiceCreate

def compute_total_amount(invoice: InvoiceCreate) -> int:
    return sum(item.subtotal for item in invoice.items)

def compute_due_date(invoice: InvoiceCreate) -> Optional[date]:
    # Si el usuario manda override, manda.
    if invoice.due_date_override:
        return invoice.due_date_override

    if invoice.payment_terms_type == "CASH":
        # Contado: puedes devolver None (y en PDF imprimir "Pago inmediato")
        return None

    # Crédito:
    days = invoice.credit_days or 0
    return invoice.issue_date + timedelta(days=days)
