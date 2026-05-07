from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models import Asociacion, Producto, Persona, Vacante, Configuracion


def obtener_totales_admin(db: Session) -> dict:
    total_asociaciones = db.query(func.count(Asociacion.id)).scalar()
    total_productos = db.query(func.count(Producto.id)).scalar()
    total_personas = db.query(func.count(Persona.id)).scalar()
    total_vacantes = db.query(func.count(Vacante.id)).filter(Vacante.fecha_limite >= datetime.now()).scalar()
    return {
        "total_asociaciones": total_asociaciones,
        "total_productos": total_productos,
        "total_personas": total_personas,
        "total_vacantes": total_vacantes,
    }


def obtener_registros_mensuales(db: Session, meses: int = 6):
    hoy = date.today()
    labels = []
    data = []
    meses_nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    for i in range(meses - 1, -1, -1):
        mes = hoy.month - i
        anio = hoy.year
        if mes <= 0:
            mes += 12
            anio -= 1
        conteo = db.query(func.count(Asociacion.id)).filter(
            extract('year', Asociacion.fecha_registro) == anio,
            extract('month', Asociacion.fecha_registro) == mes
        ).scalar()
        data.append(conteo)
        labels.append(f"{meses_nombres[mes-1]} {str(anio)[-2:]}")
    return labels, data


def obtener_ultimas_asociaciones(db: Session, limit: int = 5) -> List[Asociacion]:
    return db.query(Asociacion).order_by(Asociacion.fecha_registro.desc()).limit(limit).all()


def obtener_ultimas_vacantes(db: Session, limit: int = 5) -> List[Vacante]:
    return db.query(Vacante).order_by(Vacante.fecha_publicacion.desc()).limit(limit).all()


def listar_asociaciones_admin(db: Session) -> List[Asociacion]:
    return db.query(Asociacion).all()


def toggle_verificacion_asociacion(db: Session, email: str) -> Optional[Asociacion]:
    a = db.query(Asociacion).filter(Asociacion.email == email).first()
    if a:
        a.verificado = "" if a.verificado == "1" else "1"
        db.commit()
    return a


def obtener_asociacion_por_email(db: Session, email: str) -> Optional[Asociacion]:
    return db.query(Asociacion).filter(Asociacion.email == email).first()


def obtener_producto_por_id(db: Session, producto_id: str) -> Optional[Producto]:
    return db.query(Producto).filter(Producto.id == producto_id).first()


def actualizar_producto_admin(db: Session, producto_id: str, imagen_url: str) -> Optional[Producto]:
    p = db.query(Producto).filter(Producto.id == producto_id).first()
    if p:
        p.imagen_url = imagen_url.strip()
        db.commit()
    return p


def obtener_configuracion(db: Session) -> Configuracion:
    config = db.query(Configuracion).first()
    if not config:
        config = Configuracion()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def actualizar_configuracion(db: Session, data: dict, logo_url: str = "", favicon32: str = "", favicon16: str = "", imagen_og: str = "") -> Configuracion:
    config = db.query(Configuracion).first()
    if not config:
        config = Configuracion()
        db.add(config)
        db.commit()
        db.refresh(config)
    for key, value in data.items():
        setattr(config, key, value)
    if logo_url:
        config.logo_url = logo_url
    if favicon32:
        config.favicon_32_url = favicon32
    if favicon16:
        config.favicon_16_url = favicon16
    if imagen_og:
        config.imagen_og_url = imagen_og
    db.commit()
    return config