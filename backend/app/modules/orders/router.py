from fastapi import APIRouter
from app.routers.pedidos import router as pedidos_router
from app.routers.carrito import router as carrito_router
from app.routers.pagos import router as pagos_router
from app.routers.transportista_envios import router as transportista_envios_router

router = APIRouter()
router.include_router(pedidos_router, tags=["pedidos"])
router.include_router(carrito_router, tags=["carrito"])
router.include_router(pagos_router, prefix="/pagos", tags=["pagos"])
router.include_router(transportista_envios_router, tags=["envios"])