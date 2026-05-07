import math
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_cached_categorias
from app.services import producto_service
from app.viewmodels.producto import ProductoViewModel
from app.models.categoria import Categoria

# Ajustá esta importación según la ubicación real de tus templates
from app.main import templates

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("/")
def listar_productos(
    request: Request,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=100),
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    categorias: list = Depends(get_cached_categorias),  # lista de dicts o modelos, vos decidís
):
    productos_orm, total = producto_service.listar_productos(
        db, pagina, por_pagina, categoria_id
    )

    # Convertir a ViewModels para la plantilla
    productos_vm = [ProductoViewModel.from_orm(p) for p in productos_orm]

    total_paginas = math.ceil(total / por_pagina) if total > 0 else 1
    pagina_actual = pagina

    return templates.TemplateResponse("productos/lista.html", {
        "request": request,
        "productos": productos_vm,
        "pagina_actual": pagina_actual,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "categoria_actual": categoria_id,
        "categorias": categorias,         # para el menú lateral
        "total_productos": total,
    })


@router.get("/{producto_id}")
def detalle_producto(
    request: Request,
    producto_id: int,
    db: Session = Depends(get_db),
):
    producto = producto_service.obtener_producto_por_id(db, producto_id)
    if not producto:
        # Podrías lanzar HTTPException, yo solo redirijo o plantilla 404
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    producto_vm = ProductoViewModel.from_orm(producto)
    return templates.TemplateResponse("productos/detalle.html", {
        "request": request,
        "producto": producto_vm,
    })