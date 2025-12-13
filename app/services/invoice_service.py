from datetime import datetime
from io import BytesIO
from bson import ObjectId
from fastapi import HTTPException

from app.db.mongo import db, bucket
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.pdf_service import generate_invoice_pdf

async def create_invoice(invoice: InvoiceCreate) -> InvoiceResponse:
    pdf_bytes = generate_invoice_pdf(invoice)

    filename = f"invoice-{invoice.invoice_number}.pdf"
    pdf_file_id = await bucket.upload_from_stream(
        filename,
        pdf_bytes,
        metadata={"contentType": "application/pdf", "invoice_number": invoice.invoice_number}
    )

    doc = invoice.model_dump()
    doc.update({
        "pdf_file_id": pdf_file_id,
        "created_at": datetime.utcnow()
    })

    result = await db["invoices"].insert_one(doc)

    return InvoiceResponse(invoice_id=str(result.inserted_id), pdf_file_id=str(pdf_file_id))

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
