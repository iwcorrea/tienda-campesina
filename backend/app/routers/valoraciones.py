from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Valoracion, Pedido, ItemPedido

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

    # Verificar que el usuario haya tenido un pedido aceptado con este producto
    pedido_con_producto = (
        db.query(Pedido)
        .join(ItemPedido)
        .filter(
            Pedido.comprador_email == current_user["email"],
            Pedido.estado == "aceptado",
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