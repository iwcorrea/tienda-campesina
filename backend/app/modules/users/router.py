from fastapi import APIRouter
from app.routers import perfil, contactos, mensajes, notificaciones, transportistas, personas, asociacion, transportista_envios

router = APIRouter()
router.include_router(perfil.router)
router.include_router(contactos.router)
router.include_router(mensajes.router)
router.include_router(notificaciones.router)
router.include_router(transportistas.router)
router.include_router(personas.router)
router.include_router(asociacion.router)
router.include_router(transportista_envios.router)