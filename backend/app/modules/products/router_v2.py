from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
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
def list_products(db: Session = Depends(get_db)):
    """Devuelve todos los productos sin ningún filtro (temporal para asegurar que se ven)."""
    productos = db.query(Producto).order_by(Producto.fecha_creacion.desc()).all()
    return [_format_producto(p) for p in productos]

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _format_producto(producto)