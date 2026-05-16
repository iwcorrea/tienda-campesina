from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.dependencies import get_db
from app.models import Producto

router = APIRouter(prefix="/products", tags=["products_v2"])

@router.get("/")
def list_products(q: Optional[str] = Query(None), region: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Producto)
    if q:
        query = query.filter(Producto.nombre.ilike(f"%{q}%") | Producto.descripcion.ilike(f"%{q}%"))
    # Filtro por región (asumiendo que Producto tiene asociacion_email y Asociacion tiene region)
    if region:
        from app.models import Asociacion
        query = query.join(Asociacion, Asociacion.email == Producto.asociacion_email).filter(Asociacion.region == region)
    return query.order_by(Producto.fecha_creacion.desc()).limit(50).all()

@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto