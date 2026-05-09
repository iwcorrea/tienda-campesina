import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Contacto, SolicitudContacto, Asociacion, Persona, Transportista

# ─── Solicitudes ──────────────────────────────────
def enviar_solicitud_contacto(db: Session, solicitante_email: str, receptor_email: str) -> Optional[SolicitudContacto]:
    """Envía solicitud de contacto. Retorna None si ya existe una pendiente."""
    if solicitante_email == receptor_email:
        return None
    existente = db.query(SolicitudContacto).filter(
        SolicitudContacto.solicitante_email == solicitante_email,
        SolicitudContacto.receptor_email == receptor_email,
        SolicitudContacto.estado == "pendiente"
    ).first()
    if existente:
        return existente
    solicitud = SolicitudContacto(
        id=str(uuid.uuid4()),
        solicitante_email=solicitante_email,
        receptor_email=receptor_email
    )
    db.add(solicitud)
    db.commit()
    return solicitud

def listar_solicitudes_pendientes(db: Session, email: str) -> List[SolicitudContacto]:
    return db.query(SolicitudContacto).filter(
        SolicitudContacto.receptor_email == email,
        SolicitudContacto.estado == "pendiente"
    ).all()

def aceptar_solicitud(db: Session, solicitud_id: str, email: str) -> bool:
    solicitud = db.query(SolicitudContacto).filter(
        SolicitudContacto.id == solicitud_id,
        SolicitudContacto.receptor_email == email,
        SolicitudContacto.estado == "pendiente"
    ).first()
    if not solicitud:
        return False
    solicitud.estado = "aceptada"
    # Crear relación mutua
    agregar_contacto_directo(db, solicitud.solicitante_email, solicitud.receptor_email, "contacto")
    agregar_contacto_directo(db, solicitud.receptor_email, solicitud.solicitante_email, "contacto")
    db.commit()
    return True

def rechazar_solicitud(db: Session, solicitud_id: str, email: str) -> bool:
    solicitud = db.query(SolicitudContacto).filter(
        SolicitudContacto.id == solicitud_id,
        SolicitudContacto.receptor_email == email,
        SolicitudContacto.estado == "pendiente"
    ).first()
    if not solicitud:
        return False
    solicitud.estado = "rechazada"
    db.commit()
    return True

# ─── Contactos (bidireccionales) ─────────────────
def agregar_contacto_directo(db: Session, usuario_email: str, contacto_email: str, tipo_relacion: str = "contacto") -> Contacto:
    existe = db.query(Contacto).filter(
        Contacto.usuario_email == usuario_email,
        Contacto.contacto_email == contacto_email
    ).first()
    if existe:
        return existe
    nuevo = Contacto(
        id=str(uuid.uuid4()),
        usuario_email=usuario_email,
        contacto_email=contacto_email,
        tipo_relacion=tipo_relacion
    )
    db.add(nuevo)
    db.commit()
    return nuevo

def eliminar_contacto(db: Session, usuario_email: str, contacto_email: str) -> bool:
    """
    Elimina la relación en ambos sentidos (si existe).
    Retorna True si al menos una de las dos direcciones se eliminó.
    """
    eliminado = False
    # Dirección A → B
    c1 = db.query(Contacto).filter(
        Contacto.usuario_email == usuario_email,
        Contacto.contacto_email == contacto_email
    ).first()
    if c1:
        db.delete(c1)
        eliminado = True
    # Dirección B → A
    c2 = db.query(Contacto).filter(
        Contacto.usuario_email == contacto_email,
        Contacto.contacto_email == usuario_email
    ).first()
    if c2:
        db.delete(c2)
        eliminado = True
    if eliminado:
        db.commit()
    return eliminado

def listar_contactos(db: Session, usuario_email: str) -> List[Contacto]:
    return db.query(Contacto).filter(Contacto.usuario_email == usuario_email).all()

def obtener_info_contacto(db: Session, email: str) -> Optional[dict]:
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if asociacion:
        return {"nombre": asociacion.nombre, "tipo": "asociacion", "logo": asociacion.logo_url}
    persona = db.query(Persona).filter(Persona.email == email).first()
    if persona:
        return {"nombre": persona.nombre, "tipo": "persona", "logo": None}
    transportista = db.query(Transportista).filter(Transportista.email == email).first()
    if transportista:
        return {"nombre": transportista.nombre, "tipo": "transportista", "logo": None}
    return None