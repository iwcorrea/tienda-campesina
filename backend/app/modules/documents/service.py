"""
Servicio de dominio para la gestión documental.
"""
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.modules.documents.model import Documento
from app.modules.documents.storage import guardar_documento
from app.modules.documents.constants import DOCUMENT_TYPES

def crear_documento(
    db: Session,
    tipo: str,
    pedido_id: str,
    usuario_generador: str,
    contenido_html: str,
    metadata_extra: str = ""
) -> Optional[Documento]:
    """Genera un documento, lo sube a Cloudinary, guarda la metadata y retorna el objeto."""
    if tipo not in DOCUMENT_TYPES:
        raise ValueError(f"Tipo de documento '{tipo}' no válido")

    filename = f"{tipo}_{pedido_id}_{uuid.uuid4().hex[:8]}.html"
    folder = f"documentos/{tipo}"
    url = guardar_documento(contenido_html, filename, folder)

    documento = Documento(
        id=str(uuid.uuid4()),
        tipo=tipo,
        pedido_id=pedido_id,
        usuario_generador=usuario_generador,
        storage_url=url,
        metadata_extra=metadata_extra,
        version=1,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento

def obtener_documentos_pedido(db: Session, pedido_id: str) -> List[Documento]:
    """Retorna todos los documentos asociados a un pedido."""
    return db.query(Documento).filter(Documento.pedido_id == pedido_id).order_by(Documento.fecha_generacion.desc()).all()