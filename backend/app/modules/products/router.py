from fastapi import APIRouter
from app.routers.catalogo import router as catalogo_router
from app.routers.panel import router as panel_router
from app.routers.valoraciones import router as valoraciones_router

router = APIRouter()
router.include_router(catalogo_router, tags=["catalogo"])
router.include_router(panel_router, prefix="/panel", tags=["panel"])
router.include_router(valoraciones_router, tags=["valoraciones"])