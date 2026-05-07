import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user  # asumo que tenés get_current_user
from app.services import pedido_service
from app.viewmodels.pedido import PedidoViewModel
from app.main import templates  # ajustá si es distinto

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.get("/")
def listar_pedidos(
    request: Request,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=50),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # sesión actual
):
    # Filtramos por comprador o productor según el rol
    comprador_id = None
    productor_id = None
    if current_user.get("rol") == "comprador":
        comprador_id = current_user["id"]
    elif current_user.get("rol") == "productor":
        productor_id = current_user["productor_id"]  # asumiendo que el usuario tiene productor_id

    pedidos_orm, total = pedido_service.listar_pedidos(
        db,
        pagina=pagina,
        por_pagina=por_pagina,
        comprador_id=comprador_id,
        productor_id=productor_id,
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
def detalle_pedido(
    request: Request,
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    pedido = pedido_service.obtener_pedido_por_id(db, pedido_id)
    if not pedido:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    # Verificar que el usuario pueda ver este pedido (comprador del pedido o productor dueño)
    if (current_user["id"] != pedido.comprador_id) and (current_user.get("productor_id") != pedido.productor_id):
        return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

    pedido_vm = PedidoViewModel.from_orm(pedido)
    return templates.TemplateResponse("pedidos/detalle.html", {
        "request": request,
        "pedido": pedido_vm,
    })