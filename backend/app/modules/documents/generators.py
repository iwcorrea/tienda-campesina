"""
Generadores de contenido HTML para cada tipo de documento.
Utilizan plantillas Jinja2 ubicadas en app/modules/documents/templates/.
"""
from jinja2 import Environment, FileSystemLoader
import os

# Configurar cargador de plantillas
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def generar_html(tipo: str, datos: dict) -> str:
    """Renderiza la plantilla correspondiente al tipo de documento con los datos proporcionados."""
    template_map = {
        "factura": "factura.html",
        "remision": "remision.html",
        "cotizacion": "cotizacion.html",
        "orden_carga": "orden_carga.html",
        "comprobante_entrega": "comprobante_entrega.html",
        "contrato_basico": "contrato_basico.html",
    }
    template_name = template_map.get(tipo)
    if not template_name:
        raise ValueError(f"No hay plantilla para el tipo '{tipo}'")

    template = env.get_template(template_name)
    return template.render(**datos)