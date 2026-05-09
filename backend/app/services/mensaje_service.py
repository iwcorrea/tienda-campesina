import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from app.models import Mensaje, Asociacion, Persona, Transportista, Bloqueo

# ─── Conversaciones ─────────────────────────────
def obtener_conversaciones(db: Session, email: str) -> List[dict]:
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
            conversaciones[otro] = m

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

    resultado.sort(key=lambda x: x["fecha"], reverse=True)
    return resultado

def obtener_hilo_con_contacto(db: Session, email: str, contacto_email: str) -> List[Mensaje]:
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

# ─── Eliminación ────────────────────────────────
def eliminar_mensaje(db: Session, mensaje_id: str, email: str) -> bool:
    mensaje = db.query(Mensaje).filter(Mensaje.id == mensaje_id).first()
    if not mensaje or mensaje.remitente_email != email:
        return False
    db.delete(mensaje)
    db.commit()
    return True

def eliminar_conversacion(db: Session, email: str, contacto_email: str):
    db.query(Mensaje).filter(
        or_(
            and_(Mensaje.remitente_email == email, Mensaje.destinatario_email == contacto_email),
            and_(Mensaje.remitente_email == contacto_email, Mensaje.destinatario_email == email)
        )
    ).delete()
    db.commit()

# ─── Bloqueo ────────────────────────────────────
def bloquear_usuario(db: Session, bloqueador_email: str, bloqueado_email: str) -> bool:
    existe = db.query(Bloqueo).filter(
        Bloqueo.bloqueador_email == bloqueador_email,
        Bloqueo.bloqueado_email == bloqueado_email
    ).first()
    if existe:
        return False
    bloqueo = Bloqueo(
        id=str(uuid.uuid4()),
        bloqueador_email=bloqueador_email,
        bloqueado_email=bloqueado_email
    )
    db.add(bloqueo)
    db.commit()
    return True

def desbloquear_usuario(db: Session, bloqueador_email: str, bloqueado_email: str) -> bool:
    bloqueo = db.query(Bloqueo).filter(
        Bloqueo.bloqueador_email == bloqueador_email,
        Bloqueo.bloqueado_email == bloqueado_email
    ).first()
    if not bloqueo:
        return False
    db.delete(bloqueo)
    db.commit()
    return True

def esta_bloqueado(db: Session, email_1: str, email_2: str) -> bool:
    return db.query(Bloqueo).filter(
        or_(
            and_(Bloqueo.bloqueador_email == email_1, Bloqueo.bloqueado_email == email_2),
            and_(Bloqueo.bloqueador_email == email_2, Bloqueo.bloqueado_email == email_1)
        )
    ).first() is not None

# ─── Utilidades ─────────────────────────────────
def contar_no_leidos(db: Session, email: str) -> int:
    return (
        db.query(func.count(Mensaje.id))
        .filter(Mensaje.destinatario_email == email, Mensaje.leido == "0")
        .scalar()
    )

def obtener_nombre_usuario(db: Session, email: str) -> str:
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