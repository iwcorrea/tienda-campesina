import datetime
import io
from fastapi import UploadFile
from app.services.upload_service import upload_raw


def generar_contrato_html(
    comprador_email: str,
    asociacion_nombre: str,
    asociacion_email: str,
    producto_nombre: str,
    cantidad: int,
    precio_unitario: int,
    precio_total: int,
    fecha_entrega: str = "",
) -> str:
    fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Contrato de compraventa</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 2cm; color: #333; }}
    h1 {{ text-align: center; color: #2d6a4f; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    .footer {{ margin-top: 50px; text-align: center; font-size: 0.9em; color: #666; }}
</style></head>
<body>
    <h1>Contrato de compraventa</h1>
    <p>Fecha de emisión: {fecha_actual}</p>
    <p><strong>Vendedor:</strong> {asociacion_nombre} ({asociacion_email})</p>
    <p><strong>Comprador:</strong> {comprador_email}</p>
    <h3>Detalle del producto o servicio</h3>
    <table>
        <tr><th>Producto</th><td>{producto_nombre}</td></tr>
        <tr><th>Cantidad</th><td>{cantidad}</td></tr>
        <tr><th>Precio unitario</th><td>${precio_unitario}</td></tr>
        <tr><th>Precio total</th><td>${precio_total}</td></tr>
        <tr><th>Fecha de entrega estimada</th><td>{fecha_entrega or "Por acordar"}</td></tr>
    </table>
    <p><strong>Condiciones:</strong> Las partes acuerdan los términos anteriores según la cotización aceptada en la plataforma Tienda Campesina. Este documento sirve como constancia del acuerdo.</p>
    <div class="footer">
        <p>Generado automáticamente por Tienda Campesina - plataforma de comercio rural</p>
    </div>
</body>
</html>"""
    return html


def subir_contrato(html: str, filename: str) -> str:
    file_bytes = io.BytesIO(html.encode("utf-8"))
    file = UploadFile(filename=filename, file=file_bytes, headers={"content-type": "text/html"})
    return upload_raw(file, folder="contratos")