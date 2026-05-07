import math
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, selectinload

from app.models.productor import Productor


def listar_productores(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 12,
    activo: Optional[bool] = True,
) -> Tuple[List[Productor], int]:
    """
    Lista de productores con carga eager de sus productos (opcional, podés quitarlo si pesa mucho).
    Filtro por activos/inactivos.
    """
    query = db.query(Productor).options(
        selectinload(Productor.productos),  # Si necesitás mostrar cuántos productos tiene
    )

    if activo is not None:
        query = query.filter(Productor.activo == activo)

    total = query.count()
    offset = (pagina - 1) * por_pagina
    productores = query.order_by(Productor.nombre).offset(offset).limit(por_pagina).all()
    return productores, total


def obtener_productor_por_id(db: Session, productor_id: int) -> Optional[Productor]:
    return (
        db.query(Productor)
        .options(selectinload(Productor.productos))
        .filter(Productor.id == productor_id)
        .first()
    )