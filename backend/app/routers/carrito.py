import uuid
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Pedido, ItemPedido, Producto
from app.templates import templates

router = APIRouter(prefix="/carrito", tags=["carrito"])

def get_carrito(request: Request) -> list:
    """Obtiene la lista de items del carrito desde la sesión."""
    return request.session.get("carrito", [])

def guardar_carrito(request: Request, carrito: list):
    """Guarda la lista de items en la sesión."""
    request.session["carrito"] = carrito

@router.get("/", response_class=HTMLResponse)
def ver_carrito(request: Request):
    """Muestra el contenido del carrito."""
    carrito = get_carrito(request)
    total = sum(item["precio"] * item["cantidad"] for item in carrito)
    return templates.TemplateResponse("carrito.html", {
        "request": request,
        "carrito": carrito,
        "total": total,
        "vacio": len(carrito) == 0
    })

@router.post("/agregar/{producto_id}")
def agregar_al_carrito(
    request: Request,
    producto_id: str,
    db: Session = Depends(get_db),
):
    """Agrega un producto al carrito (cantidad inicial 1). Si ya existe, incrementa."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return RedirectResponse(url="/catalogo", status_code=303)

    carrito = get_carrito(request)
    # Buscar si ya está en el carrito
    for item in carrito:
        if item["producto_id"] == producto_id:
            item["cantidad"] += 1
            guardar_carrito(request, carrito)
            return RedirectResponse(url="/catalogo?agregado=1", status_code=303)

    # Si no está, agregar
    carrito.append({
        "producto_id": producto.id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "cantidad": 1,
        "asociacion_email": producto.asociacion_email,
        "imagen": producto.imagen_url or ""
    })
    guardar_carrito(request, carrito)
    return RedirectResponse(url="/catalogo?agregado=1", status_code=303)

@router.post("/actualizar")
def actualizar_carrito(
    request: Request,
    producto_id: str = Form(...),
    cantidad: int = Form(...),
):
    """Cambia la cantidad de un item. Si cantidad <= 0, lo elimina."""
    carrito = get_carrito(request)
    nuevo_carrito = []
    for item in carrito:
        if item["producto_id"] == producto_id:
            if cantidad > 0:
                item["cantidad"] = cantidad
                nuevo_carrito.append(item)
            # si es 0 o negativo, se omite
        else:
            nuevo_carrito.append(item)
    guardar_carrito(request, nuevo_carrito)
    return RedirectResponse(url="/carrito", status_code=303)

@router.post("/eliminar/{producto_id}")
def eliminar_del_carrito(
    request: Request,
    producto_id: str,
):
    """Elimina un producto del carrito."""
    carrito = get_carrito(request)
    carrito = [item for item in carrito if item["producto_id"] != producto_id]
    guardar_carrito(request, carrito)
    return RedirectResponse(url="/carrito", status_code=303)

@router.post("/confirmar")
def confirmar_pedido(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Convierte el carrito en uno o varios pedidos (agrupados por asociación)."""
    if not current_user or current_user.get("tipo") != "comprador":
        return RedirectResponse(url="/auth/login", status_code=303)

    carrito = get_carrito(request)
    if not carrito:
        return RedirectResponse(url="/carrito", status_code=303)

    comprador_email = current_user["email"]

    # Agrupar items por asociacion_email
    grupos = {}
    for item in carrito:
        email_asoc = item["asociacion_email"]
        if email_asoc not in grupos:
            grupos[email_asoc] = []
        grupos[email_asoc].append(item)

    # Crear un pedido por cada grupo
    for email_asoc, items in grupos.items():
        pedido = Pedido(
            id=str(uuid.uuid4()),
            comprador_email=comprador_email,
            estado="pendiente"
        )
        db.add(pedido)
        db.flush()  # para obtener pedido.id

        for item in items:
            db.add(ItemPedido(
                id=str(uuid.uuid4()),
                pedido_id=pedido.id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                precio_unitario_inicial=item["precio"]
            ))
        db.commit()

    # Limpiar carrito
    request.session["carrito"] = []

    return RedirectResponse(url="/pedidos?confirmado=1", status_code=303)