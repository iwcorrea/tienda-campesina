from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter()

@router.get("/asociacion/{email}")
def redirigir_a_perfil_publico(email: str):
    """Redirige la URL antigua de perfil de asociación al nuevo perfil público unificado."""
    return RedirectResponse(url=f"/perfil/{email}", status_code=301)