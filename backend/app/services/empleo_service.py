import uuid
import io
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models import Vacante, Aplicacion, Persona
from app.services.upload_service import upload_raw
from app.cloudinary_utils import delete_cloudinary_asset
from app.utils import utc_to_colombia


def listar_vacantes_publicas(db: Session) -> List[Vacante]:
    return (
        db.query(Vacante)
        .filter(Vacante.fecha_limite >= datetime.now(), Vacante.estado == "activa")
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
        return False

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
            "fecha": utc_to_colombia(a.fecha_aplicacion).strftime("%d/%m/%Y") if a.fecha_aplicacion else "",
        })
    return vacante, postulantes


def seleccionar_candidato(
    db: Session,
    vacante_id: str,
    email_asociacion: str,
    persona_seleccionada_email: str,
) -> Optional[Vacante]:
    vacante = db.query(Vacante).filter(
        Vacante.id == vacante_id,
        Vacante.asociacion_email == email_asociacion,
    ).first()
    if not vacante:
        return None

    aplicacion = db.query(Aplicacion).filter(
        Aplicacion.vacante_id == vacante_id,
        Aplicacion.persona_email == persona_seleccionada_email
    ).first()
    if not aplicacion:
        return None

    vacante.estado = "cubierta"
    vacante.persona_seleccionada_email = persona_seleccionada_email

    persona = db.query(Persona).filter(Persona.email == persona_seleccionada_email).first()
    nombre_persona = persona.nombre if persona else persona_seleccionada_email
    html = generar_contrato_trabajo_html(
        asociacion_nombre=email_asociacion,
        persona_nombre=nombre_persona,
        cargo=vacante.cargo,
        salario=vacante.salario,
        tipo_contrato=vacante.tipo_contrato,
        jornada=vacante.jornada,
        ubicacion=vacante.ubicacion,
    )
    filename = f"contrato_trabajo_{vacante_id}_{persona_seleccionada_email}.html"
    try:
        url = upload_raw_contrato(html, filename)
        vacante.contrato_trabajo_url = url
    except Exception:
        pass

    db.commit()
    return vacante


def generar_contrato_trabajo_html(
    asociacion_nombre: str,
    persona_nombre: str,
    cargo: str,
    salario: int,
    tipo_contrato: str,
    jornada: str,
    ubicacion: str,
) -> str:
    fecha_actual = utc_to_colombia(datetime.now(timezone.utc)).strftime("%d/%m/%Y")
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Contrato de trabajo</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 2cm; color: #333; }}
    h1 {{ text-align: center; color: #2d6a4f; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    .footer {{ margin-top: 50px; text-align: center; font-size: 0.9em; color: #666; }}
</style></head>
<body>
    <h1>Contrato de trabajo</h1>
    <p><strong>Fecha:</strong> {fecha_actual}</p>
    <p><strong>Empleador:</strong> {asociacion_nombre}</p>
    <p><strong>Trabajador:</strong> {persona_nombre}</p>
    <table>
        <tr><th>Cargo</th><td>{cargo}</td></tr>
        <tr><th>Salario</th><td>${salario if salario > 0 else 'A convenir'}</td></tr>
        <tr><th>Tipo de contrato</th><td>{tipo_contrato.replace('_', ' ').capitalize()}</td></tr>
        <tr><th>Jornada</th><td>{jornada.replace('_', ' ').capitalize()}</td></tr>
        <tr><th>Ubicación</th><td>{ubicacion}</td></tr>
    </table>
    <p>Las partes acuerdan los términos anteriores según lo publicado en la plataforma Tienda Campesina.</p>
    <div class="footer">
        <p>Generado por Tienda Campesina - Documento de contratación</p>
    </div>
</body>
</html>"""


def upload_raw_contrato(html: str, filename: str) -> str:
    file_bytes = io.BytesIO(html.encode("utf-8"))
    file = UploadFile(filename=filename, file=file_bytes, headers={"content-type": "text/html"})
    return upload_raw(file, folder="contratos_trabajo")