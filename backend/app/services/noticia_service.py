import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models import Noticia
from app.services.upload_service import upload_image
from app.cloudinary_utils import delete_cloudinary_asset


def listar_noticias_admin(db: Session) -> List[Noticia]:
    return db.query(Noticia).order_by(Noticia.fecha_publicacion.desc()).all()


def listar_noticias_publico(db: Session) -> List[Noticia]:
    return db.query(Noticia).order_by(Noticia.fecha_publicacion.desc()).all()


def obtener_noticia_por_id(db: Session, noticia_id: str) -> Optional[Noticia]:
    return db.query(Noticia).filter(Noticia.id == noticia_id).first()


def crear_noticia(
    db: Session,
    titulo: str,
    contenido: str,
    imagen: Optional[UploadFile] = None,
    fecha_publicacion_str: Optional[str] = None,
) -> Noticia:
    imagen_url = ""
    if imagen and imagen.filename:
        imagen_url = upload_image(imagen, folder="noticias")

    if fecha_publicacion_str and fecha_publicacion_str.strip():
        try:
            fecha = datetime.strptime(fecha_publicacion_str, "%Y-%m-%d")
        except ValueError:
            fecha = datetime.now(timezone.utc)
    else:
        fecha = datetime.now(timezone.utc)

    nueva = Noticia(
        id=str(uuid.uuid4()),
        titulo=titulo,
        contenido=contenido,
        imagen_url=imagen_url,
        fecha_publicacion=fecha,
    )
    db.add(nueva)
    db.commit()
    return nueva


def actualizar_noticia(
    db: Session,
    noticia_id: str,
    titulo: str,
    contenido: str,
    imagen: Optional[UploadFile] = None,
    fecha_publicacion_str: Optional[str] = None,
) -> Optional[Noticia]:
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if not noticia:
        return None

    noticia.titulo = titulo
    noticia.contenido = contenido

    if imagen and imagen.filename:
        if noticia.imagen_url:
            delete_cloudinary_asset(noticia.imagen_url, resource_type="image")
        noticia.imagen_url = upload_image(imagen, folder="noticias")

    if fecha_publicacion_str and fecha_publicacion_str.strip():
        try:
            noticia.fecha_publicacion = datetime.strptime(fecha_publicacion_str, "%Y-%m-%d")
        except ValueError:
            pass

    db.commit()
    return noticia


def eliminar_noticia(db: Session, noticia_id: str) -> bool:
    noticia = db.query(Noticia).filter(Noticia.id == noticia_id).first()
    if noticia:
        if noticia.imagen_url:
            delete_cloudinary_asset(noticia.imagen_url, resource_type="image")
        db.delete(noticia)
        db.commit()
        return True
    return False