from io import BytesIO
from datetime import date
from typing import Optional

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader

from app.schemas.invoice import InvoiceCreate

# -----------------------------
# CONFIG "FIJA" (tu empresa)
# Ideal: mover esto a settings/.env después
# -----------------------------
ISSUER_NAME = "JUAN PABLO FERNÁNDEZ GONZÁLEZ"
ISSUER_RUT = "RUT No.1.001.192.228-1"
ISSUER_CC = "C.C.No.1.001.192.228 de Bogotá"
ISSUER_ROLE = "Gerente Comercial"
ISSUER_BRAND = "CRISTETTO CAFÉ"

BANK_TEXT = (
    "Agradezco por favor consignar el valor referido a órdenes de la cuenta de ahorros No.\n"
    "94479424866. Con el banco Bancolombia. (llave: @fernandez228)"
)

FOOTER_ADDRESS = "Calle 79 No.68 H 62"
FOOTER_PHONES = "300 562 99 47 / 300 307 37 28 / 601 909 94 30"
FOOTER_EMAIL = "cristettocafe@gmail.com"

# Ruta opcional al logo (pon aquí un PNG/JPG si lo tienes)
# Ej: LOGO_PATH = "app/assets/logo_cristetto.png"
LOGO_PATH = None


# -----------------------------
# Helpers de formato
# -----------------------------
MESES = [
    "enero","febrero","marzo","abril","mayo","junio",
    "julio","agosto","septiembre","octubre","noviembre","diciembre"
]

def format_date_long_es(d: date) -> str:
    # "15 de diciembre de 2025"
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"

def format_due_date_sentence(due_date: Optional[date]) -> str:
    if not due_date:
        return ""  # contado: no imprime fecha máxima
    # "Con Fecha de pago el 4 de Enero 2026"
    # (En tu PDF, el mes va con mayúscula inicial)
    mes = MESES[due_date.month - 1].capitalize()
    return f"Con Fecha de pago el {due_date.day} de {mes} {due_date.year}"

def format_cop_with_dots(amount: int) -> str:
    # 170000 -> "170.000"
    s = f"{amount:,}".replace(",", ".")
    return s

def format_money_mcte(amount: int) -> str:
    # tu estilo: "$.170.000.oo"
    return f"$.{format_cop_with_dots(amount)}.oo"

def wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

def concept_sentence(invoice: InvoiceCreate) -> str:
    """
    Devuelve frase que SIEMPRE empieza por:
      "Suministro de ..."
    y termina con:
      - "para la empresa <NOMBRE>." si es COMPANY
      - "para <NOMBRE>." si es PERSON
    """

    # Cierre según tipo de cliente
    if invoice.client_type == "COMPANY":
        tail = f"para la empresa {invoice.client_name}."
    else:
        tail = f"para {invoice.client_name}."

    # 1 item (similar a tu formato)
    if len(invoice.items) == 1:
        it = invoice.items[0]
        qty = it.quantity

        if float(qty).is_integer():
            q_int = int(qty)
            unidad_txt = "unidad" if q_int == 1 else "unidades"

            # Si quieres un estilo cercano: "una (1) unidad..."
            prefix = "una (1) " if q_int == 1 else f"{q_int} ({q_int}) "
            return f"Suministro de {prefix}{unidad_txt} de {it.description} {tail}"

        # Si cantidad decimal
        return f"Suministro de {qty} {it.unit} de {it.description} {tail}"

    # Varios items
    parts = []
    for it in invoice.items:
        q = int(it.quantity) if float(it.quantity).is_integer() else it.quantity
        parts.append(f"{q} {it.unit} de {it.description}")
    joined = "; ".join(parts)
    return f"Suministro de {joined} {tail}"


# -----------------------------
# PDF generator (tu plantilla)
# -----------------------------
def generate_invoice_pdf(
    invoice_number: int,
    invoice: InvoiceCreate,
    total_amount: int,
    total_amount_text: str,
    due_date: Optional[date],
) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    # Márgenes aproximados a tu PDF
    left = 72
    right = w - 72
    max_width = right - left

    # ----- Logo arriba derecha -----
    # En tu PDF el logo está arriba derecha, encima de "CUENTA DE COBRO..."
    logo_x = w - 170
    logo_y = h - 130
    logo_w = 85
    logo_h = 85

    if LOGO_PATH:
        try:
            c.drawImage(ImageReader(LOGO_PATH), logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')
        except Exception:
            # fallback si falla
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(w - 72, h - 70, ISSUER_BRAND)
    else:
        # fallback: texto en lugar de logo
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(w - 72, h - 70, ISSUER_BRAND)

    # "CUENTA DE COBRO No.xxx" alineado a la derecha
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(w - 72, h - 145, f"CUENTA DE COBRO No.{invoice_number}")

    # ----- Centro: nombre empresa -----
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, h - 175, invoice.client_company_name.upper())

    # "DEBE A:"
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 215, "DEBE A:")

    # Nombre emisor + IDs (centrado y bold como tu PDF)
    y = h - 255
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w / 2, y, ISSUER_NAME); y -= 14
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, y, ISSUER_RUT); y -= 14
    c.drawCentredString(w / 2, y, ISSUER_CC); y -= 30

    # "POR CONCEPTO DE:"
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, y, "POR CONCEPTO DE:"); y -= 28

    # ----- Párrafo concepto -----
    c.setFont("Helvetica", 9)
    concept = concept_sentence(invoice)
    lines = wrap_text(concept, "Helvetica", 9, max_width)
    for line in lines:
        c.drawString(left, y, line)
        y -= 12

    y -= 18

    # ----- "Son: ..." + valor + fecha pago -----
    son_line = f"Son: {total_amount_text} colombianos ({format_money_mcte(total_amount)})/M/cte."
    due_sentence = format_due_date_sentence(due_date)
    if due_sentence:
        son_line = son_line + " " + due_sentence

    lines = wrap_text(son_line, "Helvetica", 9, max_width)
    for line in lines:
        c.drawString(left, y, line)
        y -= 12

    y -= 14

    # ----- Condiciones de pago -----
    if invoice.payment_terms_type == "CREDIT":
        # Copiando tu estilo textual (ajustable)
        credit_days = invoice.credit_days or 0
        conditions = (
            f"Condiciones de pago: Crédito a {credit_days} días calendario.- "
            f"En casos excepcionales, el plazo puede extenderse hasta 10 días adicionales (máximo 30 días)."
        )
    else:
        conditions = "Condiciones de pago: Contado. (Pago inmediato / sin crédito)."

    lines = wrap_text(conditions, "Helvetica", 9, max_width)
    for line in lines:
        c.drawString(left, y, line)
        y -= 12

    y -= 14

    # ----- Texto banco -----
    bank_lines = BANK_TEXT.split("\n")
    for bl in bank_lines:
        wrapped = wrap_text(bl, "Helvetica", 9, max_width)
        for line in wrapped:
            c.drawString(left, y, line)
            y -= 12

    y -= 14

    # "Atentamente,"
    c.setFont("Helvetica", 9)
    c.drawString(left, y, "Atentamente,")
    y -= 30

    # Firma / nombre (centrado y bold como en tu PDF)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(w / 2, y, ISSUER_NAME); y -= 12
    c.drawCentredString(w / 2, y, ISSUER_ROLE); y -= 12
    c.drawCentredString(w / 2, y, ISSUER_BRAND); y -= 30

    # Ciudad + fecha
    c.setFont("Helvetica", 9)
    c.drawCentredString(w / 2, y, f"Bogotá D.C., {format_date_long_es(invoice.issue_date)}.")
    y -= 18

    # Línea horizontal del pie
    c.line(left, y, right, y)
    y -= 16

    # Pie de página
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, y, FOOTER_ADDRESS); y -= 12
    c.drawCentredString(w / 2, y, FOOTER_PHONES); y -= 12
    c.drawCentredString(w / 2, y, FOOTER_EMAIL); y -= 12

    c.showPage()
    c.save()

    buf.seek(0)
    return buf.getvalue()
