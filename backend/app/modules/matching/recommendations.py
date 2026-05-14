"""
Generador de recomendaciones combinando scoring, proximidad y disponibilidad.
"""
from sqlalchemy.orm import Session
from app.modules.matching.scoring import puntuar_productor, puntuar_transportista
from app.modules.matching.proximity import filtrar_por_ubicacion
from app.modules.matching.availability import productos_disponibles, transportistas_activos
from app.models import Asociacion, Producto, Transportista

def recomendar_productores(db: Session, ubicacion: str = "", limite: int = 5) -> list:
    """Recomienda productores con mejor puntuación, opcionalmente filtrados por ubicación."""
    query = db.query(Asociacion).filter(Asociacion.verificado == "1")
    if ubicacion:
        emails_cercanos = filtrar_por_ubicacion(db, ubicacion, "productor")
        if emails_cercanos:
            query = query.filter(Asociacion.email.in_(emails_cercanos))
    asociaciones = query.all()
    # Calcular puntuación y ordenar
    asociaciones_punt = []
    for a in asociaciones:
        score = puntuar_productor(db, a)
        asociaciones_punt.append((a, score))
    asociaciones_punt.sort(key=lambda x: x[1], reverse=True)
    resultado = []
    for a, score in asociaciones_punt[:limite]:
        productos = productos_disponibles(db, a.email)[:3]
        resultado.append({
            "email": a.email,
            "nombre": a.nombre,
            "ubicacion": a.direccion or "Sin ubicación",
            "estrellas": score,
            "productos_count": len(a.productos),
            "productos_destacados": [p.nombre for p in productos],
        })
    return resultado

def recomendar_transportistas(db: Session, ubicacion: str = "", limite: int = 5) -> list:
    """Recomienda transportistas activos, opcionalmente filtrados por zona."""
    transportistas = transportistas_activos(db, ubicacion)
    transportistas_punt = []
    for t in transportistas:
        score = puntuar_transportista(db, t)
        transportistas_punt.append((t, score))
    transportistas_punt.sort(key=lambda x: x[1], reverse=True)
    resultado = []
    for t, score in transportistas_punt[:limite]:
        resultado.append({
            "email": t.email,
            "nombre": t.nombre,
            "tipo_vehiculo": t.tipo_vehiculo,
            "zona_cobertura": t.zona_cobertura,
            "tarifa_base": t.tarifa_base,
            "costo_km": t.costo_km,
        })
    return resultado

def recomendar_productos(db: Session, comprador_email: str = "", limite: int = 10) -> list:
    """Recomienda productos disponibles, priorizando los mejor valorados."""
    productos = db.query(Producto).join(Asociacion).filter(
        Producto.stock > 0,
        Asociacion.verificado == "1"
    ).order_by(Producto.fecha_creacion.desc()).limit(limite).all()
    resultado = []
    for p in productos:
        from app.models import Valoracion
        avg = db.query(func.avg(Valoracion.estrellas)).filter(Valoracion.producto_id == p.id).scalar() or 0.0
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio,
            "productor": p.asociacion.nombre if p.asociacion else "",
            "estrellas": round(float(avg), 1),
            "stock": p.stock,
        })
    # Ordenar por estrellas descendente
    resultado.sort(key=lambda x: x["estrellas"], reverse=True)
    return resultado[:limite]