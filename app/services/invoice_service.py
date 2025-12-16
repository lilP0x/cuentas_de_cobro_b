from datetime import datetime
from io import BytesIO
from bson import ObjectId
from fastapi import HTTPException

from app.db.mongo import db, bucket
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.pdf_service import generate_invoice_pdf
from app.services.sequence_service import get_next_sequence
from app.services.invoice_calc import compute_total_amount, compute_due_date
from app.services.num_to_words_es import cop_amount_to_text

async def create_invoice(invoice: InvoiceCreate) -> InvoiceResponse:
    invoice_number = await get_next_sequence("invoice_number")

    total_amount = compute_total_amount(invoice)
    total_amount_text = cop_amount_to_text(total_amount)
    due_date = compute_due_date(invoice)

    # Generas PDF con todo ya “cocinado”
    pdf_bytes = generate_invoice_pdf(
        invoice_number=invoice_number,
        invoice=invoice,
        total_amount=total_amount,
        total_amount_text=total_amount_text,
        due_date=due_date
    )

    filename = f"invoice-{invoice_number}.pdf"
    pdf_file_id = await bucket.upload_from_stream(
        filename,
        pdf_bytes,
        metadata={"contentType": "application/pdf", "invoice_number": invoice_number}
    )

    doc = invoice.model_dump()
    doc.update({
        "invoice_number": invoice_number,
        "total_amount": total_amount,
        "total_amount_text": total_amount_text,
        "due_date": due_date,
        "pdf_file_id": pdf_file_id,
        "created_at": datetime.utcnow()
    })

    result = await db["invoices"].insert_one(doc)

    return InvoiceResponse(
        invoice_id=str(result.inserted_id),
        invoice_number=invoice_number,
        pdf_file_id=str(pdf_file_id),
        total_amount=total_amount,
        total_amount_text=total_amount_text,
        due_date=due_date
    )

async def get_invoice_pdf_stream(invoice_id: str):
    try:
        _id = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    invoice = await db["invoices"].find_one({"_id": _id})
    if not invoice:
        raise HTTPException(status_code=404, detail="No existe la cuenta de cobro")

    pdf_file_id = invoice.get("pdf_file_id")
    if not pdf_file_id:
        raise HTTPException(status_code=500, detail="Cuenta sin PDF asociado")

    buffer = BytesIO()
    await bucket.download_to_stream(pdf_file_id, buffer)
    buffer.seek(0)

    filename = f"invoice-{invoice.get('invoice_number','sin-numero')}.pdf"
    return buffer, filename
