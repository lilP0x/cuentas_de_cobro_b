# pdf_utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import date
from schemas import InvoiceCreate


def generate_invoice_pdf(invoice: InvoiceCreate) -> bytes:
    """
    Genera un PDF en memoria con los datos de la cuenta de cobro.
    Retorna los bytes del PDF.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 80, "CUENTA DE COBRO")

    # Datos básicos
    c.setFont("Helvetica", 11)
    y = height - 130

    c.drawString(50, y, f"Fecha: {invoice.issue_date.isoformat()}")
    y -= 18
    c.drawString(50, y, f"No.: {invoice.invoice_number}")
    y -= 30

    c.drawString(50, y, f"Cliente: {invoice.client_name}")
    y -= 18
    c.drawString(50, y, f"NIT/Documento: {invoice.client_id}")
    y -= 30

    # Concepto
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Concepto:")
    y -= 18
    c.setFont("Helvetica", 11)

    # División por líneas si el concepto es largo
    max_width = 500
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = invoice.concept.split(" ")
    line = ""
    for word in words:
        test_line = (line + " " + word).strip()
        if stringWidth(test_line, "Helvetica", 11) < max_width:
            line = test_line
        else:
            c.drawString(60, y, line)
            y -= 15
            line = word
    if line:
        c.drawString(60, y, line)
        y -= 25

    # Valor
    c.setFont("Helvetica-Bold", 12)
    amount_str = f"${invoice.amount:,.0f} COP".replace(",", ".")
    c.drawRightString(width - 50, y, f"Valor: {amount_str}")
    y -= 60

    # Firma
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "Firma:")
    y -= 50
    c.drawString(50, y, "______________________________")
    y -= 15
    c.drawString(50, y, "Prestador de servicios")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()
