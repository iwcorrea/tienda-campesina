"""
Validaciones de reglas de negocio para documentos.
"""
from app.modules.documents.constants import DOCUMENT_TYPES, DOCUMENT_STATUS

def tipo_documento_valido(tipo: str) -> bool:
    return tipo in DOCUMENT_TYPES

def estado_documento_valido(estado: str) -> bool:
    return estado in DOCUMENT_STATUS