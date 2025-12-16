from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.v1 import router
from app.services.invoice_service import get_invoice_pdf_stream
from app.schemas.client import ClientCreate, ClientResponse



router = APIRouter()


@router.post("", response_model=ClientResponse)
async def create(client: ClientCreate):
    return await ClientCreate(client)


@router.get("/{client_id}/pdf")
async def get_client(client_id: str):
    stream, filename = await get_invoice_pdf_stream(client_id)
    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )