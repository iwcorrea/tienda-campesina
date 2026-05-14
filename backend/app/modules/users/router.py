from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.routers import perfil, contactos, mensajes, notificaciones, transportistas, personas, asociacion, transportista_envios

router = APIRouter()
router.include_router(perfil.router)
router.include_router(contactos.router)
router.include_router(mensajes.router)
router.include_router(notificaciones.router)
router.include_router(transportistas.router)
router.include_router(personas.router)
router.include_router(transportista_envios.router)

# Redirección legacy: /asociacion/{email} → /perfil/{email}
@router.get("/asociacion/{email}")
def redirigir_perfil(email: str):
    return RedirectResponse(url=f"/perfil/{email}", status_code=301)