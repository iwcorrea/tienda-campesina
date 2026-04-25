from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..dependencies import templates

router = APIRouter(tags=["publico"])

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Forzar la carga directa sin usar caché
    template = templates.env.get_template("index.html")
    return HTMLResponse(content=template.render({"request": request}))

@router.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request, db: Session = Depends(get_db)):
    asociaciones = db.query(models.Asociacion).all()
    template = templates.env.get_template("catalogo.html")
    return HTMLResponse(content=template.render({"request": request, "asociaciones": asociaciones}))

@router.get("/asociacion/{asociacion_id}", response_class=HTMLResponse)
def perfil_publico(request: Request, asociacion_id: int, db: Session = Depends(get_db)):
    asociacion = db.query(models.Asociacion).filter(models.Asociacion.id == asociacion_id).first()
    if not asociacion:
        template = templates.env.get_template("404.html")
        return HTMLResponse(content=template.render({"request": request}), status_code=404)
    productos = db.query(models.Producto).filter(models.Producto.asociacion_id == asociacion_id).all()
    template = templates.env.get_template("perfil_publico.html")
    return HTMLResponse(content=template.render({"request": request, "asociacion": asociacion, "productos": productos}))