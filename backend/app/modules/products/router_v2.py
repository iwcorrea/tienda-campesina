from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.dependencies import get_db, get_current_user
from app.models import Producto, Asociacion
from .catalog import listar_productos_catalogo, obtener_producto_por_id

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
    productos = listar_productos_catalogo(db)

    if q:
        q_lower = q.lower()
        productos = [p for p in productos if
                     q_lower in p.nombre.lower() or
                     (p.descripcion and q_lower in p.descripcion.lower())]

    effective_region = region or (current_user.get("region") if current_user else None)
    if effective_region:
        productos = [p for p in productos if p.asociacion and p.asociacion.region == effective_region]

    start = (page - 1) * per_page
    return [_format_producto(p) for p in productos[start:start + per_page]]

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = obtener_producto_por_id(db, product_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _format_producto(producto)