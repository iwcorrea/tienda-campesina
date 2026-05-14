import math
from typing import Optional
from fastapi import APIRouter, Request, Form, Query, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.pedido_service import (
    listar_pedidos,
    obtener_pedido_por_id,
    listar_cotizaciones_enviadas,
)
from app.viewmodels.pedido import PedidoViewModel, CotizacionEnviadaViewModel
from app.templates import templates
from app.models import Producto, Pedido, ItemPedido
from app.modules.orders.model import OrderEvent   # <-- corregido
from app.modules.notifications.service import crear_notificacion
from app.modules.orders.events import registrar_evento
import uuid

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.get("/", response_class=HTMLResponse)
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

    comprador_email = current_user.get("email") if current_user.get("tipo") in ("comprador", "persona") else None

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


@router.get("/cotizaciones-enviadas", response_class=HTMLResponse)
def cotizaciones_enviadas(
    request: Request,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(15, ge=1, le=50),
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    comprador_email = current_user.get("email")
    items, total = listar_cotizaciones_enviadas(
        db,
        comprador_email=comprador_email,
        pagina=pagina,
        por_pagina=por_pagina,
        estado=estado,
    )

    items_vm = [CotizacionEnviadaViewModel.from_orm(item) for item in items]
    total_paginas = math.ceil(total / por_pagina) if total else 1

    return templates.TemplateResponse("pedidos/cotizaciones_enviadas.html", {
        "request": request,
        "items": items_vm,
        "pagina_actual": pagina,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "estado_actual": estado or "",
        "total_items": total,
    })


@router.get("/{pedido_id}", response_class=HTMLResponse)
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

    if current_user.get("email") != pedido.comprador_email:
        pertenece = any(
            item.producto and item.producto.asociacion_email == current_user.get("email")
            for item in pedido.items
        )
        if not pertenece:
            return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

    pedido_vm = PedidoViewModel.from_orm(pedido)
    eventos = db.query(OrderEvent).filter(OrderEvent.pedido_id == pedido_id).order_by(OrderEvent.fecha.asc()).all()

    return templates.TemplateResponse("pedidos/detalle.html", {
        "request": request,
        "pedido": pedido_vm,
        "eventos": eventos,
    })


@router.get("/{pedido_id}/eventos")
def obtener_eventos(pedido_id: str, db: Session = Depends(get_db)):
    eventos = db.query(OrderEvent).filter(OrderEvent.pedido_id == pedido_id).order_by(OrderEvent.fecha.asc()).all()
    return [
        {
            "id": e.id,
            "tipo": e.tipo,
            "descripcion": e.descripcion,
            "usuario_email": e.usuario_email,
            "estado_anterior": e.estado_anterior,
            "estado_nuevo": e.estado_nuevo,
            "fecha": e.fecha.strftime("%d/%m/%Y %H:%M") if e.fecha else None,
        }
        for e in eventos
    ]


@router.post("/cotizar-servicio/{producto_id}")
def cotizar_servicio(
    request: Request,
    producto_id: str,
    cantidad: int = Form(1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto or producto.tipo != "servicio":
        return RedirectResponse(url="/catalogo", status_code=303)

    comprador_email = current_user["email"]

    pedido = Pedido(
        id=str(uuid.uuid4()),
        comprador_email=comprador_email,
        estado="pendiente"
    )
    db.add(pedido)
    db.flush()

    db.add(ItemPedido(
        id=str(uuid.uuid4()),
        pedido_id=pedido.id,
        producto_id=producto.id,
        cantidad=cantidad,
        precio_unitario_inicial=producto.precio
    ))
    db.commit()

    registrar_evento(db, pedido.id, "order_created", usuario_email=comprador_email, estado_nuevo="pendiente", descripcion="Pedido de servicio creado")

    crear_notificacion(
        db,
        destinatario_email=producto.asociacion_email,
        remitente_email=comprador_email,
        texto=f"📋 Nueva solicitud de cotización para el servicio '{producto.nombre}' de {comprador_email}.",
        producto_id=producto.id
    )

    crear_notificacion(
        db,
        destinatario_email=comprador_email,
        remitente_email=comprador_email,
        texto=f"✅ Solicitaste cotización para '{producto.nombre}'. La asociación te responderá pronto.",
        producto_id=producto.id
    )

    return RedirectResponse(url="/pedidos?servicio_cotizado=1", status_code=303)