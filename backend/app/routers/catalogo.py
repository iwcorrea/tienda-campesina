import math
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.catalogo_service import listar_productos_catalogo, obtener_valoraciones_por_productos
from app.viewmodels.catalogo import ProductoCatalogoViewModel
from app.templates import templates   # usamos la instancia global

router = APIRouter()


@router.get("/catalogo", response_class=HTMLResponse)
def catalogo(
    request: Request,
    q: str = Query(default=None),
    tipo: str = Query(default=None),
    tipo_precio: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
):
    per_page = 6
    productos_db, total_productos = listar_productos_catalogo(
        db,
        pagina=page,
        por_pagina=per_page,
        q=q,
        tipo=tipo,
        tipo_precio=tipo_precio,
    )

    total_pages = max(1, math.ceil(total_productos / per_page))
    page = min(page, total_pages)

    # Obtenemos todas las valoraciones en una sola consulta
    ids = [p.id for p in productos_db]
    valoraciones = obtener_valoraciones_por_productos(db, ids)

    # Construimos los ViewModels
    productos_vm = []
    for p in productos_db:
        prom, num = valoraciones.get(p.id, (0.0, 0))
        productos_vm.append(ProductoCatalogoViewModel.from_orm(p, prom, num))

    return templates.TemplateResponse("catalogo.html", {
        "request": request,
        "productos": productos_vm,
        "q": q or "",
        "tipo": tipo or "",
        "tipo_precio": tipo_precio or "",
        "page": page,
        "total_pages": total_pages,
        "total_productos": total_productos,
    })