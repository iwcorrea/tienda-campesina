"""
Router del módulo orders.
Por ahora actúa como wrapper de los routers legacy (pedidos, carrito, pagos)
para mantener la compatibilidad mientras se migran los endpoints uno a uno.
"""
from fastapi import APIRouter
from app.routers import pedidos, carrito, pagos

router = APIRouter()
router.include_router(pedidos.router)
router.include_router(carrito.router)
router.include_router(pagos.router)