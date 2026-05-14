from sqlalchemy.orm import Session
from app.modules.matching.recommendations import (
    recomendar_productores,
    recomendar_transportistas,
    recomendar_productos,
)

def obtener_recomendaciones(db: Session, ubicacion: str = "", tipo: str = "todos") -> dict:
    """Servicio principal de matching."""
    result = {"productores": [], "transportistas": [], "productos": []}
    if tipo in ("todos", "productores"):
        result["productores"] = recomendar_productores(db, ubicacion)
    if tipo in ("todos", "transportistas"):
        result["transportistas"] = recomendar_transportistas(db, ubicacion)
    if tipo in ("todos", "productos"):
        result["productos"] = recomendar_productos(db)
    return result