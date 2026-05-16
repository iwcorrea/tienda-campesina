from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Pedido
from datetime import datetime, timezone

router = APIRouter(prefix="/dashboard", tags=["dashboard_v2"])

@router.get("/")
def get_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    email = current_user["email"]
    tipo = current_user["tipo"]
    data = {"activeOrders": 0, "todayDeliveries": 0}
    now = datetime.now(timezone.utc)
    if tipo == "comprador":
        data["activeOrders"] = db.query(Pedido).filter(Pedido.comprador_email == email, Pedido.estado != "entregado").count()
    elif tipo == "asociacion":
        # Simplificado: contar pedidos donde la asociación es vendedora (vía items)
        from app.models import ItemPedido
        data["activeOrders"] = db.query(Pedido).join(ItemPedido).filter(ItemPedido.producto.has(asociacion_email=email)).filter(Pedido.estado != "entregado").count()
    # entregas de hoy
    data["todayDeliveries"] = db.query(Pedido).filter(Pedido.estado == "entregado", Pedido.fecha_creacion >= now.date()).count()
    return data