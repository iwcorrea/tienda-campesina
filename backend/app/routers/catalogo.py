import logging
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Producto, Asociacion, Valoracion

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger("catalogo")

@router.get("/catalogo", response_class=HTMLResponse)
def catalogo(
    request: Request,
    q: str = Query(default=None),
    tipo: str = Query(default=None),
    tipo_precio: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db)
):
    query = db.query(Producto).join(Asociacion).filter(Asociacion.verificado == "1")
    if q:
        search = f"%{q}%"
        query = query.filter(
            (Producto.nombre.ilike(search)) | (Producto.descripcion.ilike(search))
        )
    if tipo:
        query = query.filter(Producto.tipo == tipo)
    if tipo_precio:
        query = query.filter(Producto.tipo_precio == tipo_precio)

    total_productos = query.count()
    per_page = 6
    total_pages = max(1, (total_productos + per_page - 1) // per_page)
    page = min(page, total_pages)
    productos_db = query.order_by(Producto.fecha_creacion.desc()).offset((page - 1) * per_page).limit(per_page).all()

    productos = []
    for p in productos_db:
        estrellas_data = db.query(
            func.avg(Valoracion.estrellas), func.count(Valoracion.id)
        ).filter(Valoracion.producto_id == p.id).first()
        promedio = round(float(estrellas_data[0]), 1) if estrellas_data[0] else 0
        num = estrellas_data[1]
        asociacion = p.asociacion
        productos.append({
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen_url or "https://placehold.co/300x200/5B8C51/white?text=Producto",
            "asociacion": asociacion.email,
            "asociacion_nombre": asociacion.nombre,
            "logo_url": asociacion.logo_url or "",
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio,
            "estrellas": promedio,
            "num_valoraciones": num,
            "show_whatsapp": asociacion.show_whatsapp,
            "telefono": asociacion.telefono
        })

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "productos": productos,
        "q": q or "",
        "tipo": tipo or "",
        "tipo_precio": tipo_precio or "",
        "page": page,
        "total_pages": total_pages,
        "total_productos": total_productos
    })