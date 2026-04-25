from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Asociacion, Producto

router = APIRouter(tags=["publico"])
templates = Jinja2Templates(directory="backend/app/templates")


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/catalogo")
def catalogo(request: Request, db: Session = Depends(get_db)):
    asociaciones = db.query(Asociacion).all()
    productos = db.query(Producto).all()
    return templates.TemplateResponse(
        "catalogo.html",
        {
            "request": request,
            "asociaciones": asociaciones,
            "productos": productos,
        },
    )


@router.get("/asociacion/{id}")
def perfil_publico(id: int, request: Request, db: Session = Depends(get_db)):
    asociacion = db.query(Asociacion).filter(Asociacion.id == id).first()
    productos = db.query(Producto).filter(Producto.asociacion_id == id).all()
    return templates.TemplateResponse(
        "perfil_publico.html",
        {
            "request": request,
            "asociacion": asociacion,
            "productos": productos,
        },
    )
