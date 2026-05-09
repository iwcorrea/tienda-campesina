import uuid
from sqlalchemy.orm import Session
from app.models import NotificacionSistema

def crear_notificacion(
    db: Session,
    destinatario_email: str,
    remitente_email: str,
    texto: str,
    producto_id: str = None,
):
    """
    Crea una notificación del sistema (no interfiere con la mensajería personal).
    Se mantiene la firma anterior para no tocar los lugares que la invocan.
    """
    notif = NotificacionSistema(
        id=str(uuid.uuid4()),
        destinatario_email=destinatario_email,
        texto=texto,
        url=f"/mensajes/{uuid.uuid4()}"  # URL genérica; luego podemos personalizar
    )
    db.add(notif)
    db.commit()
    return notif