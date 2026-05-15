import uuid
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Pedido, ItemPedido, Producto
from app.templates import templates
from app.modules.notifications.service import crear_notificacion
from app.modules.orders.events import registrar_evento
from app.modules.orders.service import change_order_state
from app.modules.orders.models import OrderState

router = APIRouter(prefix="/carrito", tags=["carrito"])

def get_carrito(request: Request) -> list:
    return request.session.get("carrito", [])

def guardar_carrito(request: Request, carrito: list):
    request.session["carrito"] = carrito

@router.get("/", response_class=HTMLResponse)
def ver_carrito(request: Request):
    carrito = get_carrito(request)
    total = sum(item["precio"] * item["cantidad"] for item in carrito)
    return templates.TemplateResponse("carrito.html", {
        "request": request,
        "carrito": carrito,
        "total": total,
        "vacio": len(carrito) == 0
    })

@router.post("/agregar/{producto_id}")
def agregar_al_carrito(request: Request, producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return RedirectResponse(url="/catalogo", status_code=303)
    if producto.tipo == "servicio":
        return RedirectResponse(url="/catalogo?error=servicio_no_valido", status_code=303)

    carrito = get_carrito(request)
    for item in carrito:
        if item["producto_id"] == producto_id:
            item["cantidad"] += 1
            guardar_carrito(request, carrito)
            return RedirectResponse(url="/catalogo?agregado=1", status_code=303)

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
def actualizar_carrito(request: Request, producto_id: str = Form(...), cantidad: int = Form(...)):
    carrito = get_carrito(request)
    nuevo_carrito = []
    for item in carrito:
        if item["producto_id"] == producto_id:
            if cantidad > 0:
                item["cantidad"] = cantidad
                nuevo_carrito.append(item)
        else:
            nuevo_carrito.append(item)
    guardar_carrito(request, nuevo_carrito)
    return RedirectResponse(url="/carrito", status_code=303)

@router.post("/eliminar/{producto_id}")
def eliminar_del_carrito(request: Request, producto_id: str):
    carrito = get_carrito(request)
    carrito = [item for item in carrito if item["producto_id"] != producto_id]
    guardar_carrito(request, carrito)
    return RedirectResponse(url="/carrito", status_code=303)

@router.post("/confirmar")
def confirmar_pedido(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    carrito = get_carrito(request)
    if not carrito:
        return RedirectResponse(url="/carrito", status_code=303)

    comprador_email = current_user["email"]

    grupos = {}
    for item in carrito:
        email_asoc = item["asociacion_email"]
        if email_asoc not in grupos:
            grupos[email_asoc] = []
        grupos[email_asoc].append(item)

    for email_asoc, items in grupos.items():
        pedido = Pedido(
            id=str(uuid.uuid4()),
            comprador_email=comprador_email,
            estado=OrderState.DRAFT.value      # "pendiente"
        )
        db.add(pedido)
        db.flush()

        # Primer registro de estado
        change_order_state(
            db=db,
            pedido=pedido,
            new_state=OrderState.DRAFT.value,
            changed_by=comprador_email,
            extra_data={"evento": "creación desde carrito"}
        )

        for item in items:
            db.add(ItemPedido(
                id=str(uuid.uuid4()),
                pedido_id=pedido.id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                precio_unitario_inicial=item["precio"]
            ))

        db.commit()

        registrar_evento(db, pedido.id, "order_created", usuario_email=comprador_email,
                         estado_nuevo=OrderState.DRAFT.value, descripcion="Pedido creado desde el carrito")
        crear_notificacion(db, email_asoc, "order_created", pedido.id,
                           {"comprador_email": comprador_email, "pedido_id": pedido.id})

    crear_notificacion(db, comprador_email, "order_created",
                       pedido.id if 'pedido' in locals() else "",
                       {"comprador_email": comprador_email})
    request.session["carrito"] = []
    return RedirectResponse(url="/pedidos?confirmado=1", status_code=303)