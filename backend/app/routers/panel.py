from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.dependencies import get_db, get_current_user
from app.services.panel_service import (
    obtener_asociacion_y_productos,
    crear_producto,
    actualizar_producto,
    eliminar_producto,
    listar_favoritos,
    agregar_favorito as agregar_fav,
    eliminar_favorito as eliminar_fav,
    obtener_items_cotizacion_asociacion,
    obtener_item_para_responder,
    guardar_respuesta_cotizacion,
    cancelar_cotizacion_aceptada,
    reenviar_enlace_pago,
)
from app.services.transporte_service import asignar_transportista_a_pedido
from app.services.notificacion_service import crear_notificacion
from app.viewmodels.panel import PanelViewModel, ProductoPanelViewModel
from app.templates import templates
from app.models import Producto, Pedido, Transportista, ItemPedido, ValoracionComprador
from app.services.inventario_service import (
    listar_inventario_asociacion,
    obtener_movimientos_producto,
    entrada_stock,
    salida_stock_manual,
)

router = APIRouter()


@router.get("/panel", response_class=HTMLResponse)
def panel(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    asociacion = obtener_asociacion_y_productos(db, current_user["email"])
    if not asociacion:
        return RedirectResponse(url="/auth/login", status_code=303)

    panel_vm = PanelViewModel.from_orm(asociacion)
    return templates.TemplateResponse("panel.html", {
        "request": request,
        "usuario": panel_vm.usuario,
        "productos": [p.__dict__ for p in panel_vm.productos],
    })


@router.post("/panel/producto")
def crear_producto_post(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),
    tipo_precio: str = Form("fijo"),
    imagen: UploadFile = File(None),
    stock_inicial: int = Form(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    crear_producto(
        db,
        email=current_user["email"],
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        tipo=tipo,
        tipo_precio=tipo_precio,
        imagen_file=imagen,
        stock_inicial=stock_inicial,
    )
    return RedirectResponse(url="/panel", status_code=303)


@router.get("/panel/producto/editar/{producto_id}", response_class=HTMLResponse)
def editar_producto_form(
    request: Request,
    producto_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    p = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.asociacion_email == current_user["email"]
    ).first()
    if not p:
        return RedirectResponse(url="/panel", status_code=303)

    producto_vm = ProductoPanelViewModel.from_orm(p)
    return templates.TemplateResponse("editar_producto.html", {
        "request": request,
        "producto": {
            "id": producto_vm.id,
            "nombre": producto_vm.nombre,
            "descripcion": producto_vm.descripcion,
            "precio": producto_vm.precio,
            "imagen_url": producto_vm.imagen_url,
            "tipo": producto_vm.tipo,
            "tipo_precio": producto_vm.tipo_precio,
        }
    })


@router.post("/panel/producto/actualizar/{producto_id}")
def actualizar_producto_post(
    request: Request,
    producto_id: str,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    precio: int = Form(...),
    tipo: str = Form("producto"),
    tipo_precio: str = Form("fijo"),
    imagen: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    result = actualizar_producto(
        db,
        email=current_user["email"],
        producto_id=producto_id,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        tipo=tipo,
        tipo_precio=tipo_precio,
        imagen_file=imagen,
    )
    if not result:
        return RedirectResponse(url="/panel", status_code=303)

    return RedirectResponse(url="/panel?editado=1", status_code=303)


@router.post("/panel/producto/eliminar/{producto_id}")
def eliminar_producto_post(
    request: Request,
    producto_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    eliminar_producto(db, email=current_user["email"], producto_id=producto_id)
    return RedirectResponse(url="/panel?eliminado=1", status_code=303)


@router.get("/panel/cotizaciones", response_class=HTMLResponse)
def panel_cotizaciones(
    request: Request,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    items = obtener_items_cotizacion_asociacion(db, current_user["email"])

    reputaciones = {}
    compradores_unicos = set()
    for item in items:
        email_comp = item["pedido"]["comprador_email"]
        if email_comp:
            compradores_unicos.add(email_comp)

    for email_comp in compradores_unicos:
        avg = db.query(func.avg(ValoracionComprador.estrellas)).filter(
            ValoracionComprador.comprador_email == email_comp
        ).scalar()
        reputaciones[email_comp] = round(float(avg), 1) if avg else None

    if estado == "pendiente":
        items = [i for i in items if not i["respuesta_aceptada"]]
    elif estado == "aceptada":
        items = [i for i in items if i["respuesta_aceptada"] and i.get("pedido_estado") != "pagado"]
    elif estado == "pagada":
        items = [i for i in items if i.get("pedido_estado") == "pagado"]

    return templates.TemplateResponse("panel_cotizaciones.html", {
        "request": request,
        "items": items,
        "reputaciones": reputaciones,
        "estado_actual": estado or "",
    })


@router.get("/panel/cotizacion/responder/{item_id}", response_class=HTMLResponse)
def responder_cotizacion_form(
    request: Request,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    item_obj = obtener_item_para_responder(db, item_id, current_user["email"])
    if not item_obj:
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)

    return templates.TemplateResponse("panel_responder_cotizacion.html", {
        "request": request,
        "item": item_obj,
    })


@router.post("/panel/cotizacion/responder/{item_id}")
def procesar_respuesta_cotizacion(
    request: Request,
    item_id: str,
    aceptado: str = Form(...),
    precio_contraoferta: int = Form(0),
    cantidad_contraoferta: int = Form(0),
    fecha_entrega: str = Form(""),
    mensaje: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    guardar_respuesta_cotizacion(
        db,
        item_id=item_id,
        email_asociacion=current_user["email"],
        aceptado=aceptado,
        precio_contraoferta=precio_contraoferta,
        cantidad_contraoferta=cantidad_contraoferta,
        fecha_entrega=fecha_entrega,
        mensaje=mensaje,
    )
    return RedirectResponse(url="/panel/cotizaciones?respondida=1", status_code=303)


@router.post("/panel/cotizacion/eliminar/{item_id}")
def eliminar_cotizacion(
    request: Request,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    item = db.query(ItemPedido).join(Producto).filter(
        ItemPedido.id == item_id,
        Producto.asociacion_email == current_user["email"]
    ).first()

    if not item:
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)

    pedido = item.pedido
    db.delete(item)
    db.commit()

    if pedido and len(pedido.items) == 0:
        db.delete(pedido)
        db.commit()

    return RedirectResponse(url="/panel/cotizaciones?eliminada=1", status_code=303)


@router.post("/panel/cotizacion/cancelar-aceptada/{item_id}")
def cancelar_aceptada(
    request: Request,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    cancelar_cotizacion_aceptada(db, item_id, current_user["email"])
    return RedirectResponse(url="/panel/cotizaciones?cancelada=1", status_code=303)


@router.post("/panel/pedido/reenviar-pago/{pedido_id}")
def reenviar_pago(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    reenviar_enlace_pago(db, pedido_id, current_user["email"])
    return RedirectResponse(url="/panel/cotizaciones?reenviado=1", status_code=303)


@router.get("/panel/asignar-transportista/{pedido_id}", response_class=HTMLResponse)
def asignar_transportista_form(
    request: Request,
    pedido_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)

    tiene_producto = any(
        item.producto and item.producto.tipo == "producto"
        for item in pedido.items
    )
    if not tiene_producto:
        return RedirectResponse(url="/panel/cotizaciones?error=solo_servicios", status_code=303)

    transportistas = db.query(Transportista).filter(Transportista.activo == "1").all()

    return templates.TemplateResponse("panel_asignar_transportista.html", {
        "request": request,
        "pedido": pedido,
        "transportistas": transportistas,
    })


@router.post("/panel/asignar-transportista/{pedido_id}")
def asignar_transportista_procesar(
    request: Request,
    pedido_id: str,
    transportista_id: str = Form(...),
    costo_envio: int = Form(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    tiene_producto = any(
        item.producto and item.producto.tipo == "producto"
        for item in pedido.items
    )
    if not tiene_producto:
        return RedirectResponse(url="/panel/cotizaciones?error=solo_servicios", status_code=303)

    resultado = asignar_transportista_a_pedido(
        db, pedido_id, transportista_id, current_user["email"], costo_envio
    )
    if not resultado:
        return RedirectResponse(url="/panel/cotizaciones?error=asignacion", status_code=303)

    transportista = db.query(Transportista).filter(Transportista.id == transportista_id).first()
    if transportista:
        crear_notificacion(
            db,
            destinatario_email=transportista.email,
            remitente_email=current_user["email"],
            texto=f"Se te ha asignado un nuevo envío (Pedido #{pedido_id[:8]}). Costo de envío: ${costo_envio:,}.",
        )

    return RedirectResponse(url="/panel/cotizaciones?transportista_asignado=1", status_code=303)


# ─── INVENTARIO ────────────────────────────────────
@router.get("/panel/inventario", response_class=HTMLResponse)
def panel_inventario(
    request: Request,
    producto_id: str = None,
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    inventario = listar_inventario_asociacion(db, current_user["email"])
    inventario = [p for p in inventario if p["tipo"] == "producto"]

    movimientos = []
    producto_seleccionado = None
    total_movimientos = 0

    if producto_id:
        movimientos, total_movimientos = obtener_movimientos_producto(
            db, producto_id, current_user["email"], pagina
        )
        producto_seleccionado = db.query(Producto).filter(Producto.id == producto_id).first()

    return templates.TemplateResponse("panel_inventario.html", {
        "request": request,
        "inventario": inventario,
        "movimientos": movimientos,
        "producto_seleccionado": producto_seleccionado,
        "total_movimientos": total_movimientos,
        "pagina_actual": pagina,
    })


@router.post("/panel/inventario/ajustar")
def ajustar_inventario(
    request: Request,
    producto_id: str = Form(...),
    tipo: str = Form(...),
    cantidad: int = Form(...),
    referencia: str = Form("ajuste manual"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    if tipo == "entrada":
        entrada_stock(db, producto_id, cantidad, referencia, current_user["email"])
    elif tipo == "salida":
        salida_stock_manual(db, producto_id, cantidad, referencia, current_user["email"])

    return RedirectResponse(url=f"/panel/inventario?producto_id={producto_id}", status_code=303)


# ─── TRANSPORTISTAS FAVORITOS ──────────────────────
@router.get("/panel/transportistas-favoritos", response_class=HTMLResponse)
def listar_favoritos_view(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    favoritos, todos = listar_favoritos(db, current_user["email"])
    return templates.TemplateResponse("panel_transportistas_favoritos.html", {
        "request": request,
        "favoritos": favoritos,
        "transportistas": todos,
    })


@router.post("/panel/transportistas-favoritos/agregar")
def agregar_favorito_view(
    request: Request,
    transportista_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    agregar_fav(db, current_user["email"], transportista_id)
    return RedirectResponse(url="/panel/transportistas-favoritos", status_code=303)


@router.post("/panel/transportistas-favoritos/eliminar/{favorito_id}")
def eliminar_favorito_view(
    request: Request,
    favorito_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    eliminar_fav(db, current_user["email"], favorito_id)
    return RedirectResponse(url="/panel/transportistas-favoritos", status_code=303)


# ─── API CALCULAR ENVÍO ─
@router.get("/api/calcular-envio/{asociacion_email}")
def calcular_envio(
    asociacion_email: str,
    distancia: float = Query(0),
    peso: float = Query(0),
    db: Session = Depends(get_db),
):
    from app.models import Transportista
    transportistas = db.query(Transportista).filter(Transportista.activo == "1").all()
    resultados = []
    for t in transportistas:
        costo = t.tarifa_base + (t.costo_km * distancia) + (peso * 200)
        resultados.append({
            "nombre": t.nombre,
            "medio": t.tipo_vehiculo,
            "telefono": t.telefono,
            "costo_estimado": round(costo),
            "tipo": "transportista",
        })
    return resultados