import datetime
import io
import uuid
from datetime import timezone
from fastapi import UploadFile
from app.services.upload_service import upload_raw
from app.utils import utc_to_colombia


def generar_factura_html(
    numero_factura: str,
    comprador_email: str,
    asociacion_nombre: str,
    asociacion_email: str,
    items: list,
    total: int,
) -> str:
    fecha_actual = utc_to_colombia(datetime.datetime.now(timezone.utc)).strftime("%d/%m/%Y")
    lineas = ""
    for item in items:
        lineas += f"<tr><td>{item['producto_nombre']}</td><td>{item['cantidad']}</td><td>${item['precio_unitario']}</td><td>${item['subtotal']}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Factura {numero_factura}</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 2cm; color: #333; }}
    h1 {{ text-align: center; color: #2d6a4f; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    .footer {{ margin-top: 50px; text-align: center; font-size: 0.9em; color: #666; }}
</style></head>
<body>
    <h1>Factura de venta</h1>
    <p><strong>N° Factura:</strong> {numero_factura}</p>
    <p><strong>Fecha:</strong> {fecha_actual}</p>
    <p><strong>Vendedor:</strong> {asociacion_nombre} ({asociacion_email})</p>
    <p><strong>Comprador:</strong> {comprador_email}</p>
    <h3>Detalle</h3>
    <table>
        <thead><tr><th>Producto</th><th>Cant.</th><th>Precio unit.</th><th>Subtotal</th></tr></thead>
        <tbody>{lineas}</tbody>
        <tfoot><tr><td colspan="3"><strong>Total</strong></td><td><strong>${total}</strong></td></tr></tfoot>
    </table>
    <div class="footer">
        <p>Documento generado por Tienda Campesina - plataforma de comercio rural</p>
    </div>
</body>
</html>"""
    return html


def generar_numero_factura() -> str:
    return f"FAC-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def subir_factura(html: str, filename: str) -> str:
    file_bytes = io.BytesIO(html.encode("utf-8"))
    file = UploadFile(filename=filename, file=file_bytes, headers={"content-type": "text/html"})
    return upload_raw(file, folder="facturas")