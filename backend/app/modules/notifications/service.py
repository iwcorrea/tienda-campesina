"""
Servicio para crear y consultar notificaciones.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.notifications.model import Notificacion
from app.modules.notifications.templates import generar_notificacion
from app.modules.notifications.dispatchers import despachar
import uuid

def crear_notificacion(
    db: Session,
    usuario_email: str,
    tipo_evento: str,
    referencia_pedido_id: Optional[str] = None,
    datos_extra: Optional[dict] = None
) -> Notificacion:
    """Crea una notificación, la personaliza con plantilla y la despacha."""
    if datos_extra is None:
        datos_extra = {}

    datos_extra["pedido_id"] = referencia_pedido_id or ""
    plantilla = generar_notificacion(tipo_evento, datos_extra)

    notif = Notificacion(
        id=str(uuid.uuid4()),
        usuario_email=usuario_email,
        tipo_evento=tipo_evento,
        canal="in_app",
        titulo=plantilla["titulo"],
        contenido=plantilla["contenido"],
        referencia_pedido_id=referencia_pedido_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Despachar por los canales correspondientes
    despachar(db, notif)

    return notif

def listar_notificaciones_usuario(db: Session, usuario_email: str, limite: int = 20) -> List[Notificacion]:
    return db.query(Notificacion).filter(
        Notificacion.usuario_email == usuario_email
    ).order_by(Notificacion.fecha_creacion.desc()).limit(limite).all()

def marcar_leida(db: Session, notificacion_id: str, usuario_email: str) -> Optional[Notificacion]:
    notif = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_email == usuario_email
    ).first()
    if notif:
        notif.estado = "read"
        from datetime import datetime, timezone
        notif.fecha_lectura = datetime.now(timezone.utc)
        db.commit()
    return notif