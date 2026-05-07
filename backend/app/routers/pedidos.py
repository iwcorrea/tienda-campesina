import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.pedido_service import listar_pedidos, obtener_pedido_por_id
from app.viewmodels.pedido import PedidoViewModel
from app.templates import templates   # <--- importación corregida

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.get("/")
def listar(
    request: Request,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=50),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    comprador_email = current_user.get("email") if current_user.get("tipo") == "comprador" else None

    pedidos_orm, total = listar_pedidos(
        db,
        pagina=pagina,
        por_pagina=por_pagina,
        comprador_email=comprador_email,
        estado=estado,
    )

    pedidos_vm = [PedidoViewModel.from_orm(p) for p in pedidos_orm]
    total_paginas = math.ceil(total / por_pagina) if total else 1

    return templates.TemplateResponse("pedidos/lista.html", {
        "request": request,
        "pedidos": pedidos_vm,
        "pagina_actual": pagina,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "estado_actual": estado,
        "total_pedidos": total,
    })


@router.get("/{pedido_id}")
def detalle(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido = obtener_pedido_por_id(db, pedido_id)
    if not pedido:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # Verificamos que el usuario pueda ver este pedido
    if current_user.get("email") != pedido.comprador_email:
        return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

    pedido_vm = PedidoViewModel.from_orm(pedido)
    return templates.TemplateResponse("pedidos/detalle.html", {
        "request": request,
        "pedido": pedido_vm,
    })