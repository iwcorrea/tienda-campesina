"""
Lógica de proximidad geográfica.
Actualmente usa coincidencia exacta de ubicación (municipio/departamento).
Preparado para integrar geolocalización real en el futuro.
"""
from sqlalchemy.orm import Session
from app.models import Asociacion, Transportista

def filtrar_por_ubicacion(db: Session, ubicacion: str, tipo: str = "productor"):
    """Retorna lista de emails que coinciden con la ubicación dada."""
    if not ubicacion:
        return []
    if tipo == "productor":
        asociaciones = db.query(Asociacion).filter(
            Asociacion.direccion.ilike(f"%{ubicacion}%")
        ).all()
        return [a.email for a in asociaciones]
    elif tipo == "transportista":
        transportistas = db.query(Transportista).filter(
            Transportista.zona_cobertura.ilike(f"%{ubicacion}%")
        ).all()
        return [t.email for t in transportistas]
    return []