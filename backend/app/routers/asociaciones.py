from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Asociacion

router = APIRouter(tags=["asociaciones"])
templates = Jinja2Templates(directory="backend/app/templates")


def current_user_dependency(request: Request, db: Session = Depends(get_db)) -> Asociacion:
    return get_current_user(request, db)


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    productos = (
        db.query(Asociacion)
        .filter(Asociacion.id == current_user.id)
        .first()
        .productos
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "usuario": current_user, "productos": productos},
    )


@router.get("/mi-perfil")
def mi_perfil_form(
    request: Request,
    current_user: Asociacion = Depends(current_user_dependency),
):
    return templates.TemplateResponse(
        "editar_perfil.html",
        {"request": request, "usuario": current_user},
    )


@router.post("/mi-perfil")
def mi_perfil_post(
    request: Request,
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    db: Session = Depends(get_db),
    current_user: Asociacion = Depends(current_user_dependency),
):
    usuario_db = db.query(Asociacion).filter(Asociacion.id == current_user.id).first()
    usuario_db.nombre_asociacion = nombre_asociacion
    usuario_db.descripcion = descripcion
    usuario_db.direccion = direccion
    usuario_db.telefono = telefono
    db.commit()

    return RedirectResponse(url="/mi-perfil", status_code=status.HTTP_303_SEE_OTHER)
