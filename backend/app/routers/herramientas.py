from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY
import io
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/herramientas/contrato", response_class=HTMLResponse)
def generar_contrato_form(request: Request):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("generar_contrato.html", {"request": request})

@router.post("/herramientas/contrato")
def generar_contrato_pdf(
    request: Request,
    comprador: str = Form(...),
    vendedor: str = Form(...),
    producto: str = Form(...),
    cantidad: str = Form(...),
    precio_unitario: str = Form(...),
    fecha_entrega: str = Form(...),
    condiciones: str = Form(None)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    # Normalizar precios
    def parse_num(s):
        s = s.strip().replace(" ", "")
        if not s:
            return 0.0
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return 0.0

    precio_unit = parse_num(precio_unitario)
    precio_total = precio_unit * parse_num(cantidad)

    # Crear PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "CONTRATO DE COMPRAVENTA")

    # Fecha
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 80, f"Fecha: {datetime.date.today().strftime('%d de %B de %Y')}")

    # Cláusulas
    y = height - 120
    estilo = {
        "comprador": comprador,
        "vendedor": vendedor,
        "producto": producto,
        "cantidad": cantidad,
        "precio_unit": format_price(precio_unit),
        "precio_total": format_price(precio_total),
        "fecha_entrega": fecha_entrega,
        "condiciones": condiciones or "Ninguna"
    }

    lineas = [
        f"Entre el vendedor {estilo['vendedor']} y el comprador {estilo['comprador']} se celebra el presente contrato de compraventa conforme a las siguientes cláusulas:",
        "",
        "PRIMERA: OBJETO. El vendedor se obliga a vender y entregar al comprador, y este a comprar y recibir, el siguiente producto:",
        f"Producto: {estilo['producto']}",
        f"Cantidad: {estilo['cantidad']}",
        "",
        "SEGUNDA: PRECIO. El precio acordado es el siguiente:",
        f"Precio unitario: $ {estilo['precio_unit']}",
        f"Precio total: $ {estilo['precio_total']}",
        "",
        "TERCERA: PLAZO Y LUGAR DE ENTREGA. El vendedor se obliga a entregar el producto en el lugar y fecha siguientes:",
        f"Fecha de entrega: {estilo['fecha_entrega']}. Lugar: a convenir entre las partes.",
        "",
        "CUARTA: OBLIGACIONES DEL VENDEDOR. El vendedor garantiza que el producto cumple con las condiciones de calidad e inocuidad exigidas por la ley colombiana.",
        "",
        "QUINTA: OBLIGACIONES DEL COMPRADOR. El comprador se obliga a pagar el precio total en la fecha de entrega, salvo pacto en contrario.",
        "",
        "SEXTA: INCUMPLIMIENTO Y CLÁUSULA PENAL. En caso de incumplimiento de cualquiera de las partes, la parte cumplida podrá exigir el pago de una suma equivalente al 20% del valor del contrato como cláusula penal, sin perjuicio de reclamar daños y perjuicios adicionales.",
        "",
        "SÉPTIMA: RESOLUCIÓN DE CONFLICTOS. Cualquier diferencia que surja entre las partes será resuelta preferiblemente mediante arreglo directo; en su defecto, por la jurisdicción ordinaria colombiana.",
        "",
        "OCTAVA: CONDICIONES ADICIONALES.",
        estilo['condiciones'],
        "",
        "Para constancia se firma el presente contrato a los ____ días del mes de __________ de __________.",
        "",
        "________________________                   ________________________",
        "VENDEDOR                                      COMPRADOR",
        "C.C.                                       C.C."
    ]

    for linea in lineas:
        if y < 50:
            p.showPage()
            y = height - 50
        if linea.startswith("_"):
            continue
        p.setFont("Helvetica", 11)
        p.drawString(50, y, linea)
        y -= 16

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=contrato_compraventa.pdf"}
    )

def format_price(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")