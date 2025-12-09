# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime
from io import BytesIO

from db import database, gridfs_bucket
from schemas import InvoiceCreate, InvoiceResponse
from pdf_utils import generate_invoice_pdf

app = FastAPI(title="Facturación - Cuentas de cobro")


# Helper para validar ObjectId
def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")


@app.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate):
    """
    Crea una cuenta de cobro:
    1) Genera el PDF
    2) Lo guarda en GridFS
    3) Guarda metadata en la colección invoices
    """
    # 1. Generar PDF en memoria
    pdf_bytes = generate_invoice_pdf(invoice)

    # 2. Guardar PDF en GridFS
    filename = f"invoice-{invoice.invoice_number}.pdf"
    pdf_file_id = await gridfs_bucket.upload_from_stream(
        filename,
        pdf_bytes,
        metadata={
            "contentType": "application/pdf",
            "invoice_number": invoice.invoice_number
        }
    )

    # 3. Guardar metadata en colección invoices
    invoice_doc = {
        "client_name": invoice.client_name,
        "client_id": invoice.client_id,
        "invoice_number": invoice.invoice_number,
        "issue_date": invoice.issue_date,
        "amount": invoice.amount,
        "concept": invoice.concept,
        "pdf_file_id": pdf_file_id,
        "created_at": datetime.utcnow()
    }

    result = await database["invoices"].insert_one(invoice_doc)

    return InvoiceResponse(
        invoice_id=str(result.inserted_id),
        pdf_file_id=str(pdf_file_id)
    )


@app.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str):
    """
    Devuelve el PDF asociado a una cuenta de cobro.
    """
    _id = to_object_id(invoice_id)

    invoice = await database["invoices"].find_one({"_id": _id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Cuenta de cobro no encontrada")

    pdf_file_id = invoice.get("pdf_file_id")
    if not pdf_file_id:
        raise HTTPException(status_code=500, detail="Cuenta de cobro sin PDF asociado")

    # Descargar desde GridFS a un buffer
    buffer = BytesIO()
    await gridfs_bucket.download_to_stream(pdf_file_id, buffer)
    buffer.seek(0)

    filename = f'invoice-{invoice.get("invoice_number", "sin-numero")}.pdf'

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
