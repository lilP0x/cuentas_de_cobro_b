from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app.schemas.invoice import InvoiceCreate

def generate_invoice_pdf(invoice: InvoiceCreate) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h-80, "CUENTA DE COBRO")

    c.setFont("Helvetica", 11)
    y = h - 130
    c.drawString(50, y, f"Fecha: {invoice.issue_date.isoformat()}"); y -= 18
    c.drawString(50, y, f"No.: {invoice.invoice_number}"); y -= 30
    c.drawString(50, y, f"Cliente: {invoice.client_name}"); y -= 18
    c.drawString(50, y, f"NIT/Documento: {invoice.client_id}"); y -= 30
    c.drawString(50, y, "Concepto:"); y -= 18
    c.drawString(60, y, invoice.concept); y -= 30
    c.drawRightString(w-50, y, f"Valor: ${invoice.amount:,.0f} COP".replace(",", "."))

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
