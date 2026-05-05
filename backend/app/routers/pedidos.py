import uuid
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Producto, Pedido, ItemPedido, RespuestaCotizacion, Mensaje
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ─── AGREGAR AL CARRITO (sesión) ───────────────────
@router.post("/pedido/agregar-item")
def agregar_item(
    request: Request,
    producto_id: str = Form(...),
    cantidad: int = Form(1),
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return RedirectResponse(url="/catalogo", status_code=303)

    carrito = request.session.get("carrito", [])
    for item in carrito:
        if item["producto_id"] == producto_id:
            item["cantidad"] += cantidad
            break
    else:
        carrito.append({
            "producto_id": producto_id,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "asociacion_email": producto.asociacion_email,
            "asociacion_nombre": producto.asociacion.nombre if producto.asociacion else "",
            "cantidad": cantidad
        })
    request.session["carrito"] = carrito
    return RedirectResponse(url="/catalogo", status_code=303)

# ─── VER CARRITO ───────────────────────────────────
@router.get("/pedido/ver", response_class=HTMLResponse)
def ver_pedido(request: Request):
    carrito = request.session.get("carrito", [])
    return templates.TemplateResponse("pedido_ver.html", {
        "request": request,
        "items": carrito,
        "total_items": len(carrito)
    })

# ─── ENVIAR COTIZACIÓN (crear pedido formal) ───────
@router.post("/pedido/enviar-cotizacion")
def enviar_cotizacion(request: Request, db: Session = Depends(get_db)):
    carrito = request.session.get("carrito", [])
    if not carrito:
        return RedirectResponse(url="/catalogo", status_code=303)
    email = request.session["usuario"]
    pedido = Pedido(comprador_email=email)
    db.add(pedido)
    db.flush()

    # Para evitar enviar múltiples mensajes a la misma asociación, agrupamos
    asociaciones_notificadas = set()

    for item in carrito:
        nuevo_item = ItemPedido(
            pedido_id=pedido.id,
            producto_id=item["producto_id"],
            cantidad=item["cantidad"],
            precio_unitario_inicial=item["precio"]
        )
        db.add(nuevo_item)

        # Notificar a la asociación dueña del producto (solo una vez)
        asoc_email = item["asociacion_email"]
        if asoc_email and asoc_email not in asociaciones_notificadas:
            msg = Mensaje(
                id=str(uuid.uuid4()),
                remitente_email=email,
                destinatario_email=asoc_email,
                texto=f"Has recibido una nueva solicitud de cotización (Pedido #{pedido.id[:8]}). Revisa tu panel de cotizaciones.",
                leido="0"
            )
            db.add(msg)
            asociaciones_notificadas.add(asoc_email)

    request.session["carrito"] = []
    db.commit()
    return RedirectResponse(url="/mis-pedidos", status_code=303)

# ─── MIS PEDIDOS (comprador) ───────────────────────
@router.get("/mis-pedidos", response_class=HTMLResponse)
def mis_pedidos(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    pedidos = db.query(Pedido).filter(Pedido.comprador_email == email).order_by(Pedido.fecha_creacion.desc()).all()
    return templates.TemplateResponse("mis_pedidos.html", {"request": request, "pedidos": pedidos})

# ─── DETALLE DE PEDIDO (comprador) ────────────────
@router.get("/mis-pedidos/{pedido_id}", response_class=HTMLResponse)
def detalle_pedido(request: Request, pedido_id: str, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.comprador_email != request.session.get("usuario"):
        return RedirectResponse(url="/mis-pedidos", status_code=303)
    return templates.TemplateResponse("pedido_detalle.html", {"request": request, "pedido": pedido})

# ─── CONFIRMAR PEDIDO (comprador) ──────────────────
@router.post("/mis-pedidos/{pedido_id}/confirmar")
def confirmar_pedido(request: Request, pedido_id: str, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id, Pedido.comprador_email == request.session.get("usuario")).first()
    if pedido:
        pedido.estado = "confirmado"
        db.commit()
    return RedirectResponse(url=f"/mis-pedidos/{pedido_id}", status_code=303)

# ─── PANEL COTIZACIONES (asociación) ───────────────
@router.get("/panel/cotizaciones", response_class=HTMLResponse)
def panel_cotizaciones(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    items_con_respuesta = db.query(ItemPedido).join(Producto).filter(
        Producto.asociacion_email == email
    ).all()
    return templates.TemplateResponse("panel_cotizaciones.html", {
        "request": request,
        "items": items_con_respuesta
    })

# ─── RESPONDER A UN ÍTEM (asociación) ──────────────
@router.get("/panel/cotizacion/responder/{item_id}", response_class=HTMLResponse)
def form_responder_cotizacion(request: Request, item_id: str, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    item = db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
    if not item or item.producto.asociacion_email != request.session.get("usuario"):
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)
    return templates.TemplateResponse("panel_responder_cotizacion.html", {
        "request": request,
        "item": item
    })

@router.post("/panel/cotizacion/responder/{item_id}")
def responder_cotizacion(
    request: Request,
    item_id: str,
    aceptado: str = Form("pendiente"),
    precio_contraoferta: int = Form(0),
    cantidad_contraoferta: int = Form(0),
    fecha_entrega: str = Form(""),
    mensaje: str = Form(""),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    item = db.query(ItemPedido).filter(ItemPedido.id == item_id).first()
    if not item or item.producto.asociacion_email != email:
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)

    respuesta = RespuestaCotizacion(
        item_pedido_id=item_id,
        asociacion_email=email,
        aceptado=aceptado,
        precio_contraoferta=precio_contraoferta,
        cantidad_contraoferta=cantidad_contraoferta,
        fecha_entrega_contraoferta=fecha_entrega,
        mensaje=mensaje
    )
    db.add(respuesta)
    db.flush()

    # Notificar al comprador sobre la respuesta
    comprador_email = item.pedido.comprador_email
    if comprador_email:
        notificacion = Mensaje(
            id=str(uuid.uuid4()),
            remitente_email=email,
            destinatario_email=comprador_email,
            texto=f"Tu cotización para '{item.producto.nombre}' ha recibido una respuesta ({aceptado}). Revisa el detalle del pedido #{item.pedido.id[:8]}.",
            leido="0"
        )
        db.add(notificacion)

    db.commit()
    return RedirectResponse(url="/panel/cotizaciones", status_code=303)