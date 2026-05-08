from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Valoracion, ValoracionComprador, Pedido, ItemPedido

router = APIRouter(prefix="/valoraciones", tags=["valoraciones"])

@router.post("/crear/{producto_id}")
def crear_valoracion(
    request: Request,
    producto_id: str,
    estrellas: int = Form(...),
    comentario: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido_con_producto = (
        db.query(Pedido)
        .join(ItemPedido)
        .filter(
            Pedido.comprador_email == current_user["email"],
            Pedido.estado.in_(["aceptado", "entregado"]),
            ItemPedido.producto_id == producto_id
        )
        .first()
    )
    if not pedido_con_producto:
        return RedirectResponse(url="/catalogo?error=no_comprado", status_code=303)

    nueva = Valoracion(
        producto_id=producto_id,
        estrellas=estrellas,
        comentario=comentario or "",
        email_usuario=current_user["email"]
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/catalogo?valora_ok=1", status_code=303)


@router.post("/comprador/{pedido_id}")
def valorar_comprador(
    request: Request,
    pedido_id: str,
    comprador_email: str = Form(...),
    estrellas: int = Form(...),
    comentario: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return RedirectResponse(url="/panel/cotizaciones?error=pedido", status_code=303)

    pertenece = False
    for item in pedido.items:
        if item.producto and item.producto.asociacion_email == current_user["email"]:
            pertenece = True
            break
    if not pertenece:
        return RedirectResponse(url="/panel/cotizaciones?error=pertenencia", status_code=303)

    if pedido.estado not in ("aceptado", "entregado"):
        return RedirectResponse(url="/panel/cotizaciones?error=estado", status_code=303)

    existente = db.query(ValoracionComprador).filter(
        ValoracionComprador.pedido_id == pedido_id,
        ValoracionComprador.asociacion_email == current_user["email"],
        ValoracionComprador.comprador_email == comprador_email
    ).first()
    if existente:
        return RedirectResponse(url="/pedidos?error=ya_valorado", status_code=303)

    nueva = ValoracionComprador(
        comprador_email=comprador_email,
        asociacion_email=current_user["email"],
        pedido_id=pedido_id,
        estrellas=estrellas,
        comentario=comentario or "",
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/panel/cotizaciones?comprador_valorado=1", status_code=303)