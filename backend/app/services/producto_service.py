import math
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from app.models.producto import Producto


def listar_productos(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 12,
    categoria_id: Optional[int] = None,
) -> Tuple[List[Producto], int]:
    """
    Devuelve una lista de productos con sus relaciones (categoria, productor)
    cargadas de forma eager, paginada y opcionalmente filtrada por categoría.
    Retorna (productos, total_productos).
    """
    # Consulta base con eager loading para evitar N+1
    query = db.query(Producto).options(
        selectinload(Producto.categoria),
        selectinload(Producto.productor),
    )

    if categoria_id is not None:
        query = query.filter(Producto.categoria_id == categoria_id)

    # Total de productos (sin límite) para calcular páginas
    total = query.count()

    # Paginación
    offset = (pagina - 1) * por_pagina
    productos = query.offset(offset).limit(por_pagina).all()

    return productos, total


def obtener_producto_por_id(db: Session, producto_id: int) -> Optional[Producto]:
    """Obtiene un producto individual con relaciones cargadas."""
    return (
        db.query(Producto)
        .options(
            selectinload(Producto.categoria),
            selectinload(Producto.productor),
        )
        .filter(Producto.id == producto_id)
        .first()
    )