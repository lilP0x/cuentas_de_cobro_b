from fastapi import APIRouter
from fastapi.responses import StreamingResponse


from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.invoice_service import create_invoice, get_invoice_pdf_stream

router = APIRouter()

@router.post("", response_model=InvoiceResponse)
async def create(invoice: InvoiceCreate):
    return await create_invoice(invoice)

@router.get("/{invoice_id}/pdf")
async def get_pdf(invoice_id: str):
    stream, filename = await get_invoice_pdf_stream(invoice_id)
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )
