from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from math import ceil
from app.dependencies import get_db, get_current_user
from app.models import Producto

router = APIRouter(prefix="/products", tags=["products_v2"])

def _format_producto(producto: Producto) -> dict:
    valoraciones = producto.valoraciones
    promedio = (
        round(sum(v.estrellas for v in valoraciones) / len(valoraciones), 1)
        if valoraciones else None
    )
    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "tipo_precio": producto.tipo_precio,
        "imagen_url": producto.imagen_url or "",
        "asociacion": {
            "nombre": producto.asociacion.nombre if producto.asociacion else "Sin asociación"
        },
        "valoracion_promedio": promedio,
        "cantidad_valoraciones": len(valoraciones),
        "descripcion": producto.descripcion or "",
    }

@router.get("/")
def list_products(
    q: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Producto)

    if q:
        q_lower = q.lower()
        query = query.filter(
            (Producto.nombre.ilike(f"%{q_lower}%")) |
            (Producto.descripcion.ilike(f"%{q_lower}%"))
        )

    effective_region = region or (current_user.get("region") if current_user else None)
    if effective_region:
        from app.models import Asociacion
        query = query.join(Producto.asociacion).filter(Asociacion.region == effective_region)

    total = query.count()
    total_pages = ceil(total / per_page) if total else 0
    start = (page - 1) * per_page
    productos_pagina = query.order_by(Producto.fecha_creacion.desc()).offset(start).limit(per_page).all()

    # El frontend espera un array simple, no {data: [], meta: {}}
    return [_format_producto(p) for p in productos_pagina]

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _format_producto(producto)