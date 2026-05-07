import uuid
from sqlalchemy.orm import Session
from app.models import Mensaje


def crear_notificacion(
    db: Session,
    destinatario_email: str,
    remitente_email: str,
    texto: str,
    producto_id: str = None,
) -> Mensaje:
    """Crea un mensaje interno como notificación automática del sistema."""
    mensaje = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=remitente_email,
        destinatario_email=destinatario_email,
        producto_id=producto_id,
        texto=texto,
        leido="0"
    )
    db.add(mensaje)
    db.commit()
    return mensaje