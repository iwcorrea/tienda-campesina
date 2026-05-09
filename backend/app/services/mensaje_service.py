import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from app.models import Mensaje, Asociacion, Persona, Transportista

def obtener_conversaciones(db: Session, email: str) -> List[dict]:
    """Lista de conversaciones únicas, mostrando el último mensaje de cada contacto."""
    mensajes = (
        db.query(Mensaje)
        .filter(
            or_(Mensaje.remitente_email == email, Mensaje.destinatario_email == email)
        )
        .order_by(desc(Mensaje.fecha_envio))
        .all()
    )

    conversaciones = {}
    for m in mensajes:
        otro = m.remitente_email if m.destinatario_email == email else m.destinatario_email
        if otro not in conversaciones:
            conversaciones[otro] = m  # solo nos quedamos con el más reciente

    resultado = []
    for otro, ultimo in conversaciones.items():
        nombre = obtener_nombre_usuario(db, otro)
        resultado.append({
            "contacto_email": otro,
            "contacto_nombre": nombre,
            "ultimo_mensaje": ultimo.texto[:80] + ("..." if len(ultimo.texto) > 80 else ""),
            "fecha": ultimo.fecha_envio,
            "leido": ultimo.leido if ultimo.destinatario_email == email else "1",
            "producto_id": ultimo.producto_id,
            "mensaje_id": ultimo.id
        })

    # Ordenar por fecha descendente
    resultado.sort(key=lambda x: x["fecha"], reverse=True)
    return resultado

def obtener_hilo_con_contacto(db: Session, email: str, contacto_email: str) -> List[Mensaje]:
    """Todos los mensajes entre dos usuarios, en orden cronológico."""
    return (
        db.query(Mensaje)
        .filter(
            or_(
                and_(Mensaje.remitente_email == email, Mensaje.destinatario_email == contacto_email),
                and_(Mensaje.remitente_email == contacto_email, Mensaje.destinatario_email == email)
            )
        )
        .order_by(Mensaje.fecha_envio.asc())
        .all()
    )

def marcar_conversacion_leida(db: Session, email: str, contacto_email: str):
    """Marca como leídos todos los mensajes recibidos de un contacto."""
    db.query(Mensaje).filter(
        Mensaje.destinatario_email == email,
        Mensaje.remitente_email == contacto_email,
        Mensaje.leido == "0"
    ).update({"leido": "1"})
    db.commit()

def enviar_mensaje(
    db: Session,
    email_remitente: str,
    destinatario_email: str,
    texto: str,
    producto_id: Optional[str] = None,
) -> Mensaje:
    """Envía un mensaje y lo persiste."""
    nuevo = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=email_remitente,
        destinatario_email=destinatario_email,
        producto_id=producto_id or None,
        texto=texto,
        leido="0",
    )
    db.add(nuevo)
    db.commit()
    return nuevo

def contar_no_leidos(db: Session, email: str) -> int:
    """Cantidad de mensajes no leídos para la campanita."""
    return (
        db.query(func.count(Mensaje.id))
        .filter(Mensaje.destinatario_email == email, Mensaje.leido == "0")
        .scalar()
    )

def obtener_nombre_usuario(db: Session, email: str) -> str:
    """Nombre público del usuario (asociación, persona o transportista)."""
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        return a.nombre or email
    p = db.query(Persona).filter(Persona.email == email).first()
    if p:
        return p.nombre or email
    t = db.query(Transportista).filter(Transportista.email == email).first()
    if t:
        return t.nombre or email
    return email