from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import obtener_usuario_actual
from .. import models
from ..dependencies import templates

router = APIRouter(prefix="/asociaciones", tags=["asociaciones"])

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, usuario=Depends(obtener_usuario_actual)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "usuario": usuario})

@router.get("/mi-perfil", response_class=HTMLResponse)
def editar_perfil_form(request: Request, usuario=Depends(obtener_usuario_actual)):
    return templates.TemplateResponse("editar_perfil.html", {"request": request, "usuario": usuario})

@router.post("/mi-perfil")
def editar_perfil(
    request: Request,
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    db: Session = Depends(get_db),
    usuario=Depends(obtener_usuario_actual)
):
    usuario.nombre_asociacion = nombre_asociacion
    usuario.descripcion = descripcion
    usuario.direccion = direccion
    usuario.telefono = telefono
    db.commit()
    return RedirectResponse(url="/asociaciones/dashboard", status_code=303)