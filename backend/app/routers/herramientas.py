import io
import uuid
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion
import cloudinary.uploader
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
import urllib.request
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("herramientas")

def upload_file_cloudinary(file: UploadFile, folder: str, raw: bool = False):
    if not file or not file.filename:
        return ""
    try:
        kwargs = dict(folder=folder, filename=file.filename, use_filename=True, unique_filename=True, access_mode="public")
        if raw:
            kwargs["resource_type"] = "raw"
        result = cloudinary.uploader.upload(file.file, **kwargs)
        return result.get("secure_url", "")
    except Exception:
        return ""

@router.get("/herramientas/contrato", response_class=HTMLResponse)
def contrato_get(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    return templates.TemplateResponse("generar_contrato.html", {
        "request": request,
        "asociacion": asociacion
    })

@router.post("/herramientas/contrato/generar")
def generar_contrato_pdf(
    request: Request,
    vendedor_nombre: str = Form(...),
    vendedor_documento: str = Form(...),
    comprador_nombre: str = Form(...),
    comprador_documento: str = Form(...),
    producto: str = Form(...),
    cantidad: float = Form(...),
    precio_unitario: float = Form(...),
    fecha_entrega: str = Form(...),
    condiciones_adicionales: str = Form(""),
    logo_opcion: str = Form("asociacion"),
    logo_personalizado: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    email = request.session["usuario"]
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    logo_url = None

    if logo_opcion == "asociacion" and asociacion and asociacion.logo_url:
        logo_url = asociacion.logo_url
    elif logo_opcion == "personalizado" and logo_personalizado and logo_personalizado.filename:
        logo_url = upload_file_cloudinary(logo_personalizado, "logos_contratos")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="Contrato de Compraventa"
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('Title', parent=styles['Title'], alignment=TA_CENTER, fontSize=16, spaceAfter=12)
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=8)

    elements = []

    # ---- ENCABEZADO CON LOGO Y TÍTULO ----
    header_data = []
    if logo_url:
        try:
            with urllib.request.urlopen(logo_url) as response:
                img_data = response.read()
            img = Image(io.BytesIO(img_data), width=70, height=70)     # logo de 2.5 cm aprox
            img.hAlign = 'LEFT'
            header_data.append(img)
        except Exception as e:
            logger.warning(f"No se pudo cargar el logo desde {logo_url}: {e}")
            header_data.append("")    # celda vacía si falla el logo
    else:
        header_data.append("")

    # Celda derecha: título y fecha
    titulo_cabecera = Paragraph("CONTRATO DE COMPRAVENTA DE PRODUCTO AGRÍCOLA", style_title)
    fecha_actual = Paragraph(f"Fecha de emisión: {datetime.datetime.now().strftime('%d/%m/%Y')}", style_normal)
    header_data.append([titulo_cabecera, Spacer(1, 6), fecha_actual])

    # Construimos la tabla del encabezado: una fila, dos columnas
    header_table = Table([header_data], colWidths=[2.5*cm, 13.5*cm])   # ancho del logo 2.5cm, el resto para el texto
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (0,0), (0,0), 10),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # ---- CLÁUSULAS ----
    elements.append(Paragraph(
        f"<b>1. PARTES</b><br/>"
        f"<b>VENDEDOR:</b> {vendedor_nombre}, identificado con {vendedor_documento}.<br/>"
        f"<b>COMPRADOR:</b> {comprador_nombre}, identificado con {comprador_documento}.<br/>"
        f"Ambas partes acuerdan celebrar el presente contrato de compraventa, el cual se regirá por las siguientes cláusulas.",
        style_normal
    ))

    elements.append(Paragraph(
        f"<b>2. OBJETO</b><br/>"
        f"El VENDEDOR se obliga a transferir la propiedad y entregar al COMPRADOR los siguientes productos: "
        f"{producto}, en cantidad de {cantidad:,.0f}, a un precio unitario de ${precio_unitario:,.0f} COP.",
        style_normal
    ))

    precio_total = precio_unitario * cantidad
    elements.append(Paragraph(
        f"<b>3. PRECIO Y FORMA DE PAGO</b><br/>"
        f"El precio total del contrato asciende a la suma de ${precio_total:,.0f} COP, "
        f"que el COMPRADOR se obliga a pagar al VENDEDOR en su totalidad al momento de la firma del presente documento, "
        f"salvo pacto en contrario.",
        style_normal
    ))

    clausulas = [
        f"<b>4. PLAZO Y LUGAR DE ENTREGA</b><br/>"
        f"El VENDEDOR se obliga a entregar los productos objeto de este contrato a más tardar el día {fecha_entrega}, "
        f"en el lugar acordado por las partes o, en su defecto, en el domicilio del VENDEDOR.",
        f"<b>5. OBLIGACIONES DEL VENDEDOR</b><br/>"
        f"El VENDEDOR declara que los productos objeto de este contrato se encuentran en buen estado, "
        f"cumplen con las normas sanitarias aplicables y son de su legítima propiedad, "
        f"libres de todo gravamen o limitación.",
        f"<b>6. OBLIGACIONES DEL COMPRADOR</b><br/>"
        f"El COMPRADOR se obliga a recibir los productos en la fecha y lugar pactados y a pagar el precio acordado. "
        f"La no recepción injustificada dará lugar a la indemnización de perjuicios a favor del VENDEDOR.",
        f"<b>7. CLÁUSULA PENAL</b><br/>"
        f"En caso de incumplimiento de cualquiera de las obligaciones derivadas del presente contrato, "
        f"la parte incumplida deberá pagar a la otra una suma equivalente al 20% del valor total del contrato "
        f"como sanción, sin perjuicio de la indemnización de los daños y perjuicios causados.",
        f"<b>8. RESOLUCIÓN DE CONFLICTOS</b><br/>"
        f"Para todos los efectos legales, las partes se someten a la jurisdicción de los jueces civiles de Colombia "
        f"y renuncian expresamente a cualquier otro fuero que pudiera corresponderles.",
        f"<b>9. CONDICIONES ADICIONALES</b><br/>"
        f"{condiciones_adicionales if condiciones_adicionales.strip() else 'No se pactan condiciones adicionales.'}"
    ]
    for texto in clausulas:
        elements.append(Paragraph(texto, style_normal))
        elements.append(Spacer(1, 4))

    elements.append(Spacer(1, 20))
    data = [
        ["_________________________", "_________________________"],
        [f"{vendedor_nombre}", f"{comprador_nombre}"],
        ["VENDEDOR", "COMPRADOR"]
    ]
    table = Table(data, colWidths=[7*cm, 7*cm])
    table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    headers = {
        'Content-Disposition': f'attachment; filename="contrato_{vendedor_nombre.replace(" ", "_")}_{datetime.datetime.now().strftime("%Y%m%d")}.pdf"'
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)