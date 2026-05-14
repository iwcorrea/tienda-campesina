"""
Sistema de puntuación simple basado en reglas.
Preparado para ser reemplazado por IA en el futuro.
"""
from sqlalchemy.orm import Session
from app.models import Asociacion, Transportista, Producto, Valoracion, ValoracionComprador
from sqlalchemy import func

def puntuar_productor(db: Session, asociacion: Asociacion) -> float:
    """Calcula un puntaje para un productor basado en valoraciones, antigüedad y actividad."""
    # Promedio de valoraciones de sus productos
    avg_productos = db.query(func.avg(Valoracion.estrellas)).join(Producto).filter(
        Producto.asociacion_email == asociacion.email
    ).scalar() or 0.0

    # Promedio de valoraciones como vendedor (compradores lo valoran)
    avg_comprador = db.query(func.avg(ValoracionComprador.estrellas)).filter(
        ValoracionComprador.asociacion_email == asociacion.email
    ).scalar() or 0.0

    # Cantidad de productos activos
    productos_activos = db.query(func.count(Producto.id)).filter(
        Producto.asociacion_email == asociacion.email
    ).scalar() or 0

    # Puntaje combinado (pesos arbitrarios)
    score = (avg_productos * 0.5) + (avg_comprador * 0.3) + (min(productos_activos, 10) * 0.2)
    return round(score, 1)

def puntuar_transportista(db: Session, transportista: Transportista) -> float:
    """Puntaje basado en tarifas competitivas y antigüedad."""
    # Mientras más bajo el costo_km, mejor (inverso)
    if transportista.costo_km > 0:
        score_tarifa = max(0, 5 - (transportista.costo_km / 1000))
    else:
        score_tarifa = 3
    # Otros factores podrían ser entregas completadas, pero no tenemos aún.
    return round(score_tarifa, 1)