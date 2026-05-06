from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Asociacion, Producto, Vacante, Noticia

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request, db: Session = Depends(get_db)):
    # Estadísticas globales para generar confianza
    total_asociaciones = db.query(func.count(Asociacion.id)).scalar()
    total_productos = db.query(func.count(Producto.id)).scalar()
    total_vacantes = db.query(func.count(Vacante.id)).filter(Vacante.fecha_limite >= func.now()).scalar()

    # Últimas 3 noticias
    noticias = db.query(Noticia).order_by(Noticia.fecha_publicacion.desc()).limit(3).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "noticias": noticias,
        "total_asociaciones": total_asociaciones,
        "total_productos": total_productos,
        "total_vacantes": total_vacantes
    })

@router.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# Las rutas de sitemap y robots.txt se mantienen igual que antes