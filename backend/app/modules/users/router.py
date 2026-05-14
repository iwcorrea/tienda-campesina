from fastapi import APIRouter
from app.routers.perfil import router as perfil_router
from app.routers.contactos import router as contactos_router
from app.routers.mensajes import router as mensajes_router
from app.routers.notificaciones import router as notificaciones_router
from app.routers.transportistas import router as transportistas_router
from app.routers.personas import router as personas_router

router = APIRouter()
router.include_router(perfil_router, tags=["perfil"])
router.include_router(contactos_router, prefix="/contactos", tags=["contactos"])
router.include_router(mensajes_router, tags=["mensajes"])
router.include_router(notificaciones_router, tags=["notificaciones"])
router.include_router(transportistas_router, tags=["transportistas"])
router.include_router(personas_router, tags=["personas"])