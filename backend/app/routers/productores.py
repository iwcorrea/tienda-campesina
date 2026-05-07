import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_cached_productores_activos  # nueva dependencia
from app.services import productor_service
from app.viewmodels.productor import ProductorViewModel
from app.main import templates

router = APIRouter(prefix="/productores", tags=["productores"])


@router.get("/")
def listar_productores(
    request: Request,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    productores_activos: list = Depends(get_cached_productores_activos),  # para el menú superior
):
    # Solo listamos activos
    productores_orm, total = productor_service.listar_productores(
        db, pagina=pagina, por_pagina=por_pagina, activo=True
    )

    productores_vm = [ProductorViewModel.from_orm(p) for p in productores_orm]
    total_paginas = math.ceil(total / por_pagina) if total else 1

    return templates.TemplateResponse("productores/lista.html", {
        "request": request,
        "productores": productores_vm,
        "pagina_actual": pagina,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "total_productores": total,
        "productores_activos": productores_activos,  # para dropdown o filtro rápido
    })


@router.get("/{productor_id}")
def detalle_productor(
    request: Request,
    productor_id: int,
    db: Session = Depends(get_db),
):
    productor = productor_service.obtener_productor_por_id(db, productor_id)
    if not productor:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    productor_vm = ProductorViewModel.from_orm(productor, limit_productos=8)
    return templates.TemplateResponse("productores/detalle.html", {
        "request": request,
        "productor": productor_vm,
    })