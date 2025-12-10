# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime
import os
from io import BytesIO
from typing import List, Optional

from db import database, get_gridfs_bucket
from schemas import (
    InvoiceCreate,
    InvoiceResponse,
    ClientPdfItem,
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from pdf_utils import generate_invoice_pdf

app = FastAPI(title="Facturación - Cuentas de cobro")

# CORS: permitir orígenes configurables vía .env (ALLOWED_ORIGINS)
from fastapi.middleware.cors import CORSMiddleware
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Intentar conectar a MongoDB al iniciar y loguear un mensaje claro.

    Si la conexión falla, el servidor seguirá arriba pero las peticiones que
    dependan de la base de datos devolverán errores hasta que la conexión se
    establezca. Esto facilita el diagnóstico durante el desarrollo.
    """
    try:
        # `database` es una AsyncIOMotorDatabase; `command("ping")` es async
        await database.command("ping")
        print("MongoDB: conexión OK")
    except Exception as e:
        # No abortamos el arranque, sólo avisamos
        print("Warning: no se pudo conectar a MongoDB al iniciar:", e)


@app.get("/health")
async def health():
    """Endpoint de health-check que verifica conexión a MongoDB."""
    try:
        await database.command("ping")
        return {"status": "ok", "mongodb": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {e}")


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
    bucket = await get_gridfs_bucket()
    pdf_file_id = await bucket.upload_from_stream(
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

    # 4. Registrar/actualizar cliente en colección `clients` (guardar pdf asociado)
    # Usamos upsert para crear el registro del cliente si no existe y añadir el pdf_file_id
    await database["clients"].update_one(
        {"client_id": invoice.client_id},
        {
            "$set": {"client_name": invoice.client_name, "updated_at": datetime.utcnow()},
            "$addToSet": {"pdf_file_ids": pdf_file_id}
        },
        upsert=True
    )

    return InvoiceResponse(
        invoice_id=str(result.inserted_id),
        pdf_file_id=str(pdf_file_id)
    )


@app.get("/clients/{client_id}/pdfs", response_model=List[ClientPdfItem])
async def get_client_pdfs(client_id: str):
    """
    Devuelve la lista de PDFs (facturas) asociadas a un cliente identificado por `client_id`.
    """
    cursor = database["invoices"].find({"client_id": client_id})
    items = []
    async for inv in cursor:
        # Normalizar issue_date a date si viene como datetime
        issue_date = inv.get("issue_date")
        if hasattr(issue_date, "date"):
            try:
                issue_date = issue_date.date()
            except Exception:
                pass

        items.append(ClientPdfItem(
            invoice_id=str(inv.get("_id")),
            invoice_number=inv.get("invoice_number", ""),
            issue_date=issue_date,
            pdf_file_id=str(inv.get("pdf_file_id")) if inv.get("pdf_file_id") else "",
            amount=inv.get("amount", 0),
            concept=inv.get("concept")
        ))
    return items


@app.post("/clients", response_model=ClientResponse)
async def create_client(client: ClientCreate):
    """Crea un cliente nuevo. Usa `client_id` como identificador único (p.ej. NIT)."""
    existing = await database["clients"].find_one({"client_id": client.client_id})
    if existing:
        raise HTTPException(status_code=409, detail="Cliente ya existe")

    doc = {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "pdf_file_ids": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await database["clients"].insert_one(doc)

    # Normalizar salida
    doc["pdf_file_ids"] = [str(x) for x in doc.get("pdf_file_ids", [])]
    return ClientResponse(**doc)


@app.get("/clients", response_model=List[ClientResponse])
async def list_clients():
    """Lista todos los clientes."""
    cursor = database["clients"].find({})
    out = []
    async for c in cursor:
        out.append(ClientResponse(
            client_id=c.get("client_id"),
            client_name=c.get("client_name"),
            contact_email=c.get("contact_email"),
            phone=c.get("phone"),
            address=c.get("address"),
            pdf_file_ids=[str(x) for x in c.get("pdf_file_ids", [])]
        ))
    return out


@app.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """Obtener un cliente por su `client_id`."""
    c = await database["clients"].find_one({"client_id": client_id})
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ClientResponse(
        client_id=c.get("client_id"),
        client_name=c.get("client_name"),
        contact_email=c.get("contact_email"),
        phone=c.get("phone"),
        address=c.get("address"),
        pdf_file_ids=[str(x) for x in c.get("pdf_file_ids", [])]
    )


@app.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, payload: ClientUpdate):
    """Actualizar datos básicos de un cliente."""
    update_fields = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="Nada para actualizar")

    update_fields["updated_at"] = datetime.utcnow()
    result = await database["clients"].update_one({"client_id": client_id}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return await get_client(client_id)


@app.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    """Eliminar un cliente (no elimina facturas)."""
    result = await database["clients"].delete_one({"client_id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"deleted": True}


# ---------------- Productos CRUD ----------------
@app.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    """Crear un producto nuevo en la colección `products`."""
    # Validaciones simples
    if product.price < 0:
        raise HTTPException(status_code=400, detail="El precio debe ser >= 0")
    if product.stock < 0:
        raise HTTPException(status_code=400, detail="El stock debe ser >= 0")

    doc = {
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await database["products"].insert_one(doc)
    return ProductResponse(
        product_id=str(result.inserted_id),
        name=doc["name"],
        price=doc["price"],
        stock=doc["stock"],
    )


@app.get("/products", response_model=List[ProductResponse])
async def list_products():
    """Listar todos los productos."""
    cursor = database["products"].find({})
    out = []
    async for p in cursor:
        out.append(ProductResponse(
            product_id=str(p.get("_id")),
            name=p.get("name"),
            price=p.get("price", 0),
            stock=p.get("stock", 0),
        ))
    return out


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Obtener un producto por su ObjectId."""
    _id = to_object_id(product_id)
    p = await database["products"].find_one({"_id": _id})
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(
        product_id=str(p.get("_id")),
        name=p.get("name"),
        price=p.get("price", 0),
        stock=p.get("stock", 0),
    )


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, payload: ProductUpdate):
    """Actualizar un producto (parcial)."""
    update_fields = {k: v for k, v in payload.dict().items() if v is not None}
    if "price" in update_fields and update_fields["price"] < 0:
        raise HTTPException(status_code=400, detail="El precio debe ser >= 0")
    if "stock" in update_fields and update_fields["stock"] < 0:
        raise HTTPException(status_code=400, detail="El stock debe ser >= 0")

    update_fields["updated_at"] = datetime.utcnow()
    _id = to_object_id(product_id)
    result = await database["products"].update_one({"_id": _id}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return await get_product(product_id)


@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Eliminar un producto por su ObjectId."""
    _id = to_object_id(product_id)
    result = await database["products"].delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"deleted": True}


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
    bucket = await get_gridfs_bucket()
    await bucket.download_to_stream(pdf_file_id, buffer)
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
