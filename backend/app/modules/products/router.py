from fastapi import APIRouter
from app.routers import catalogo, panel, valoraciones

router = APIRouter()
router.include_router(catalogo.router)
router.include_router(panel.router)
router.include_router(valoraciones.router)