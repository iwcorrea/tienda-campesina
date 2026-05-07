from typing import List, Tuple, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from app.models import Producto, Valoracion


def listar_productos_catalogo(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 6,
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    tipo_precio: Optional[str] = None,
) -> Tuple[List[Producto], int]:
    """
    Devuelve productos verificados con eager loading de asociación.
    Filtra por búsqueda, tipo, tipo_precio.
    Retorna (productos, total).
    """

    # Carga eager de la asociación para evitar N+1
    query = db.query(Producto).options(
        selectinload(Producto.asociacion)
    ).join(Producto.asociacion).filter(Producto.asociacion.has(verificado="1"))

    if q:
        search = f"%{q}%"
        query = query.filter(
            (Producto.nombre.ilike(search)) | (Producto.descripcion.ilike(search))
        )
    if tipo:
        query = query.filter(Producto.tipo == tipo)
    if tipo_precio:
        query = query.filter(Producto.tipo_precio == tipo_precio)

    total = query.count()
    offset = (pagina - 1) * por_pagina
    productos = query.order_by(Producto.fecha_creacion.desc()).offset(offset).limit(por_pagina).all()

    return productos, total


def obtener_valoraciones_por_productos(db: Session, producto_ids: List[str]) -> dict:
    """
    Devuelve un diccionario {producto_id: (promedio_estrellas, num_valoraciones)}
    para una lista de IDs, haciendo una sola consulta agregada.
    """
    if not producto_ids:
        return {}

    resultados = (
        db.query(
            Valoracion.producto_id,
            func.avg(Valoracion.estrellas).label("promedio"),
            func.count(Valoracion.id).label("num")
        )
        .filter(Valoracion.producto_id.in_(producto_ids))
        .group_by(Valoracion.producto_id)
        .all()
    )

    return {
        r.producto_id: (round(float(r.promedio), 1) if r.promedio else 0, r.num)
        for r in resultados
    }