"""
Disponibilidad de productos y transportistas.
"""
from sqlalchemy.orm import Session
from app.models import Producto, Transportista

def productos_disponibles(db: Session, productor_email: str = None) -> list:
    query = db.query(Producto).filter(Producto.stock > 0)
    if productor_email:
        query = query.filter(Producto.asociacion_email == productor_email)
    return query.all()

def transportistas_activos(db: Session, zona: str = None) -> list:
    query = db.query(Transportista).filter(Transportista.activo == "1")
    if zona:
        query = query.filter(Transportista.zona_cobertura.ilike(f"%{zona}%"))
    return query.all()