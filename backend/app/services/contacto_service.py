import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Contacto, Asociacion, Persona, Transportista


def agregar_contacto(db: Session, usuario_email: str, contacto_email: str, tipo_relacion: str = "contacto") -> Contacto:
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
    contacto = db.query(Contacto).filter(
        Contacto.usuario_email == usuario_email,
        Contacto.contacto_email == contacto_email
    ).first()
    if contacto:
        db.delete(contacto)
        db.commit()
        return True
    return False


def listar_contactos(db: Session, usuario_email: str) -> List[Contacto]:
    return db.query(Contacto).filter(Contacto.usuario_email == usuario_email).all()


def obtener_info_contacto(db: Session, email: str) -> Optional[dict]:
    """Devuelve info básica del contacto según su tipo (asociación, persona, transportista)."""
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