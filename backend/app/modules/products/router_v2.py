from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.dependencies import get_db, get_current_user
from app.models import Producto, Asociacion

router = APIRouter(prefix="/products", tags=["products_v2"])

@router.get("/")
def list_products(
    q: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Producto)
    if q:
        query = query.filter(
            Producto.nombre.ilike(f"%{q}%") | Producto.descripcion.ilike(f"%{q}%")
        )
    # Determinar región: usar query param o la del usuario
    effective_region = region or (current_user.get("region") if current_user else None)
    if effective_region:
        query = query.join(Asociacion, Asociacion.email == Producto.asociacion_email).filter(
            Asociacion.region == effective_region
        )
    return query.order_by(Producto.fecha_creacion.desc()).limit(50).all()

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto