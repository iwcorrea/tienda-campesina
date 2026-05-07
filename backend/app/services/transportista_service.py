from typing import Optional
from sqlalchemy.orm import Session
from app.models import Transportista


def obtener_transportista_por_email(db: Session, email: str) -> Optional[Transportista]:
    return db.query(Transportista).filter(Transportista.email == email).first()


def actualizar_perfil_transportista(
    db: Session,
    email: str,
    nombre: str,
    telefono: Optional[str],
    tipo_vehiculo: str,
    capacidad: str,
    zona_cobertura: str,
    tarifa_base: int,
    costo_km: int,
    documento_url: Optional[str] = None,
) -> Optional[Transportista]:
    t = db.query(Transportista).filter(Transportista.email == email).first()
    if not t:
        return None
    t.nombre = nombre
    t.telefono = telefono or ""
    t.tipo_vehiculo = tipo_vehiculo
    t.capacidad = capacidad
    t.zona_cobertura = zona_cobertura
    t.tarifa_base = tarifa_base
    t.costo_km = costo_km
    if documento_url:
        t.documento_url = documento_url
    db.commit()
    return t


def listar_transportistas_activos(db: Session):
    return db.query(Transportista).filter(Transportista.activo == "1").all()