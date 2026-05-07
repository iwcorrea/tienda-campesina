from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal          # Ajusta la ruta si es distinta
from app.models.categoria import Categoria    # Modelo de Categoria
from app.models.productor import Productor    # Modelo de Productor
from app.core.cache import categoria_cache, SimpleCache


def get_db():
    """Proporciona una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cached_categorias(db: Session = Depends(get_db)) -> list:
    """
    Retorna la lista de categorías desde caché en memoria (TTL 5 min).
    Si la caché expira, se recarga desde la base de datos.
    """
    def cargar():
        categorias = db.query(Categoria).order_by(Categoria.nombre).all()
        return [{"id": c.id, "nombre": c.nombre} for c in categorias]

    return categoria_cache.get_or_set("categorias_list", cargar)


# Caché separada para productores activos (TTL 10 minutos)
productor_cache = SimpleCache(list, ttl_seconds=600)


def get_cached_productores_activos(db: Session = Depends(get_db)) -> list:
    """
    Retorna la lista de productores activos desde caché (TTL 10 min).
    Útil para menús, filtros o dropdowns que se usan en muchas páginas.
    """
    def cargar():
        productores = (
            db.query(Productor)
            .filter(Productor.activo == True)
            .order_by(Productor.nombre)
            .all()
        )
        return [{"id": p.id, "nombre": p.nombre} for p in productores]

    return productor_cache.get_or_set("productores_activos", cargar)