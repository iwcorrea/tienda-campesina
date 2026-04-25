from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..dependencies import templates

router = APIRouter(tags=["publico"])

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request, db: Session = Depends(get_db)):
    asociaciones = db.query(models.Asociacion).all()
    return templates.TemplateResponse("catalogo.html", {"request": request, "asociaciones": asociaciones})

@router.get("/asociacion/{asociacion_id}", response_class=HTMLResponse)
def perfil_publico(request: Request, asociacion_id: int, db: Session = Depends(get_db)):
    asociacion = db.query(models.Asociacion).filter(models.Asociacion.id == asociacion_id).first()
    if not asociacion:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    productos = db.query(models.Producto).filter(models.Producto.asociacion_id == asociacion_id).all()
    return templates.TemplateResponse("perfil_publico.html", {"request": request, "asociacion": asociacion, "productos": productos})