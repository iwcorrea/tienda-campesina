import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models import Vacante, Aplicacion, Persona
from app.services.upload_service import upload_raw
from app.cloudinary_utils import delete_cloudinary_asset


def listar_vacantes_publicas(db: Session) -> List[Vacante]:
    return (
        db.query(Vacante)
        .filter(Vacante.fecha_limite >= datetime.now())
        .order_by(Vacante.fecha_publicacion.desc())
        .all()
    )


def obtener_vacante_por_id(db: Session, vacante_id: str) -> Optional[Vacante]:
    return db.query(Vacante).filter(Vacante.id == vacante_id).first()


def obtener_persona_actual(db: Session, email: str) -> Optional[Persona]:
    return db.query(Persona).filter(Persona.email == email).first()


def aplicar_a_vacante(
    db: Session,
    vacante_id: str,
    persona_email: str,
    mensaje: str = "",
) -> bool:
    existente = db.query(Aplicacion).filter(
        Aplicacion.vacante_id == vacante_id,
        Aplicacion.persona_email == persona_email,
    ).first()
    if existente:
        return False   # ya aplicó

    nueva = Aplicacion(
        vacante_id=vacante_id,
        persona_email=persona_email,
        mensaje=mensaje or "",
    )
    db.add(nueva)
    db.commit()
    return True


def listar_vacantes_por_asociacion(db: Session, email: str) -> List[Vacante]:
    return (
        db.query(Vacante)
        .filter(Vacante.asociacion_email == email)
        .order_by(Vacante.fecha_publicacion.desc())
        .all()
    )


def crear_vacante(
    db: Session,
    asociacion_email: str,
    cargo: str,
    descripcion: str,
    ubicacion: str,
    salario: int,
    salario_convenir: str,
    tipo_contrato: str,
    jornada: str,
    requisitos: str,
    fecha_limite_str: str,
    terminos: Optional[UploadFile] = None,
) -> Vacante:
    try:
        fecha = datetime.strptime(fecha_limite_str, "%Y-%m-%d")
    except ValueError:
        fecha = datetime.now() + timedelta(days=30)

    salario_final = 0 if salario_convenir == "1" else salario
    terminos_url = upload_raw(terminos, folder="terminos_referencia") if terminos else ""

    nueva = Vacante(
        id=str(uuid.uuid4()),
        asociacion_email=asociacion_email,
        cargo=cargo,
        descripcion=descripcion or "",
        ubicacion=ubicacion or "",
        salario=salario_final,
        tipo_contrato=tipo_contrato,
        jornada=jornada,
        requisitos=requisitos or "",
        fecha_limite=fecha,
        terminos_url=terminos_url,
    )
    db.add(nueva)
    db.commit()
    return nueva


def eliminar_vacante(db: Session, vacante_id: str, email_asociacion: str) -> bool:
    vacante = db.query(Vacante).filter(
        Vacante.id == vacante_id,
        Vacante.asociacion_email == email_asociacion,
    ).first()
    if vacante:
        if vacante.terminos_url:
            delete_cloudinary_asset(vacante.terminos_url, resource_type="raw")
        db.delete(vacante)
        db.commit()
        return True
    return False


def obtener_postulantes(db: Session, vacante_id: str, email_asociacion: str):
    vacante = db.query(Vacante).filter(
        Vacante.id == vacante_id,
        Vacante.asociacion_email == email_asociacion,
    ).first()
    if not vacante:
        return None, []

    aplicaciones = db.query(Aplicacion).filter(Aplicacion.vacante_id == vacante_id).all()
    postulantes = []
    for a in aplicaciones:
        persona = a.persona
        postulantes.append({
            "nombre": persona.nombre if persona else "Desconocido",
            "email": persona.email if persona else "",
            "telefono": persona.telefono if persona else "",
            "hoja_vida_url": persona.hoja_vida_url if persona else "",
            "mensaje": a.mensaje,
            "fecha": a.fecha_aplicacion.strftime("%d/%m/%Y") if a.fecha_aplicacion else "",
        })
    return vacante, postulantes