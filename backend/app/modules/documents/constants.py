"""
Tipos de documentos y estados permitidos.
"""

DOCUMENT_TYPES = {
    "factura": "Factura electrónica",
    "remision": "Remisión",
    "cotizacion": "Cotización",
    "orden_carga": "Orden de carga",
    "comprobante_entrega": "Comprobante de entrega",
    "contrato_basico": "Contrato básico",
}

DOCUMENT_STATUS = {
    "generado": "Generado",
    "almacenado": "Almacenado",
    "entregado": "Entregado",
    "anulado": "Anulado",
    "version_anterior": "Versión anterior",
}