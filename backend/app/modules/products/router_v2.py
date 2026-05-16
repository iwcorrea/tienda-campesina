from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from math import ceil
from app.dependencies import get_db, get_current_user
from app.models import Producto, Asociacion, Valoracion
from app.services.catalogo_service import (
    listar_productos_catalogo,
    obtener_producto_por_id as servicio_obtener_producto,
)

router = APIRouter(prefix="/products", tags=["products_v2"])

def _format_producto(producto):
    """Formatea un objeto Producto al contrato que espera el frontend."""
    valoraciones = producto.valoraciones
    promedio = round(sum(v.estrellas for v in valoraciones) / len(valoraciones), 1) if valoraciones else None

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
    """
    Lista productos con filtros opcionales, paginado.
    Reutiliza el servicio legacy de catálogo.
    """
    # El servicio legacy espera filtros específicos; adaptamos aquí
    # para no modificar el servicio.
    # Retorna todos los productos activos, luego aplicamos búsqueda y paginación.
    productos_brutos = listar_productos_catalogo(db)  # lista de Producto

    # Filtro por búsqueda
    if q:
        q_lower = q.lower()
        productos_brutos = [p for p in productos_brutos if
                            q_lower in p.nombre.lower() or
                            (p.descripcion and q_lower in p.descripcion.lower())]

    # Filtro por región (si se pasa, o usar la del usuario)
    effective_region = region or (current_user.get("region") if current_user else None)
    if effective_region:
        productos_brutos = [p for p in productos_brutos if
                            p.asociacion and p.asociacion.region == effective_region]

    total = len(productos_brutos)
    total_pages = ceil(total / per_page) if total else 0
    start = (page - 1) * per_page
    end = start + per_page
    pagina_productos = productos_brutos[start:end]

    resultado = [_format_producto(p) for p in pagina_productos]

    return {
        "data": resultado,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
    }

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = servicio_obtener_producto(db, product_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _format_producto(producto)