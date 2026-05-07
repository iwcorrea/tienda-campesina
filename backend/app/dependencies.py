from typing import List

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal  # tu fábrica de sesiones
from app.models.categoria import Categoria
from app.core.cache import categoria_cache


def get_db():
    """Dependencia para obtener una sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cached_categorias(db: Session = Depends(get_db)) -> list:
    """
    Devuelve la lista de categorías desde caché (TTL 5 min).
    Si la caché expira, recarga de la BD.
    """
    def cargar():
        categorias = db.query(Categoria).order_by(Categoria.nombre).all()
        # Convertir a diccionarios o lo que necesite la plantilla
        return [
            {"id": c.id, "nombre": c.nombre}
            for c in categorias
        ]
    return categoria_cache.get_or_set("categorias_list", cargar)