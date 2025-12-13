from fastapi import APIRouter
from app.api.v1.invoices import router as invoices_router

api_router = APIRouter()
api_router.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
