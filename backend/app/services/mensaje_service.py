import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Mensaje, Asociacion, Persona, Transportista

def obtener_bandeja_entrada(db: Session, email: str) -> List[Mensaje]:
    return (
        db.query(Mensaje)
        .filter(Mensaje.destinatario_email == email)
        .order_by(Mensaje.fecha_envio.desc())
        .all()
    )

def obtener_bandeja_salida(db: Session, email: str) -> List[Mensaje]:
    return (
        db.query(Mensaje)
        .filter(Mensaje.remitente_email == email)
        .order_by(Mensaje.fecha_envio.desc())
        .all()
    )

def obtener_mensaje_por_id(db: Session, mensaje_id: str, email: str) -> Optional[Mensaje]:
    return (
        db.query(Mensaje)
        .filter(
            Mensaje.id == mensaje_id,
            (Mensaje.destinatario_email == email) | (Mensaje.remitente_email == email),
        )
        .first()
    )

def marcar_como_leido(db: Session, mensaje: Mensaje, email: str):
    if mensaje.destinatario_email == email and mensaje.leido == "0":
        mensaje.leido = "1"
        db.commit()

def obtener_hilo(db: Session, mensaje: Mensaje) -> List[Mensaje]:
    respuestas = (
        db.query(Mensaje)
        .filter(Mensaje.mensaje_padre_id == mensaje.id)
        .order_by(Mensaje.fecha_envio.asc())
        .all()
    )
    return [mensaje] + respuestas

def responder_mensaje(
    db: Session,
    mensaje_original: Mensaje,
    email_remitente: str,
    texto: str,
) -> Mensaje:
    destinatario = (
        mensaje_original.remitente_email
        if mensaje_original.remitente_email != email_remitente
        else mensaje_original.destinatario_email
    )
    nuevo = Mensaje(
        id=str(uuid.uuid4()),
        remitente_email=email_remitente,
        destinatario_email=destinatario,
        producto_id=mensaje_original.producto_id,
        texto=texto,
        leido="0",
        mensaje_padre_id=mensaje_original.id,
    )
    db.add(nuevo)
    db.commit()
    return nuevo

def enviar_mensaje_nuevo(
    db: Session,
    email_remitente: str,
    destinatario_email: str,
    texto: str,
    producto_id: Optional[str] = None,
) -> Mensaje:
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
    return (
        db.query(func.count(Mensaje.id))
        .filter(Mensaje.destinatario_email == email, Mensaje.leido == "0")
        .scalar()
    )

def obtener_nombre_usuario(db: Session, email: str) -> str:
    """Devuelve el nombre público del usuario según su tipo, o el email si no se encuentra."""
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