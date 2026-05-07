from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

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
    obtener_item_para_responder,        # <-- nuevo
    guardar_respuesta_cotizacion,       # <-- nuevo
)
from app.viewmodels.panel import PanelViewModel, ProductoPanelViewModel
from app.templates import templates
from app.models import Producto   # necesario para editar producto

router = APIRouter()


# ─── PANEL PRINCIPAL ──────────────────────────────
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


# ─── CREAR PRODUCTO ───────────────────────────────
@router.post("/panel/producto")
def crear_producto_post(
    request: Request,
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

    crear_producto(
        db,
        email=current_user["email"],
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        tipo=tipo,
        tipo_precio=tipo_precio,
        imagen_file=imagen,
    )
    return RedirectResponse(url="/panel", status_code=303)


# ─── EDITAR PRODUCTO (GET) ─────────────────────────
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


# ─── ACTUALIZAR PRODUCTO ───────────────────────────
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

    return RedirectResponse(url="/panel", status_code=303)


# ─── ELIMINAR PRODUCTO ─────────────────────────────
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
    return RedirectResponse(url="/panel", status_code=303)


# ─── COTIZACIONES RECIBIDAS ────────────────────────
@router.get("/panel/cotizaciones", response_class=HTMLResponse)
def panel_cotizaciones(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    items = obtener_items_cotizacion_asociacion(db, current_user["email"])
    return templates.TemplateResponse("panel_cotizaciones.html", {
        "request": request,
        "items": items,
    })


# ─── RESPONDER COTIZACIÓN (GET) ────────────────────
@router.get("/panel/cotizacion/responder/{item_id}", response_class=HTMLResponse)
def responder_cotizacion_form(
    request: Request,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    item_data = obtener_item_para_responder(db, item_id, current_user["email"])
    if not item_data:
        return RedirectResponse(url="/panel/cotizaciones", status_code=303)

    return templates.TemplateResponse("panel_responder_cotizacion.html", {
        "request": request,
        "item": item_data,
    })


# ─── PROCESAR RESPUESTA (POST) ─────────────────────
@router.post("/panel/cotizacion/responder/{item_id}")
def procesar_respuesta_cotizacion(
    request: Request,
    item_id: str,
    aceptado: str = Form(...),                     # "aceptado", "rechazado", "contraoferta"
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