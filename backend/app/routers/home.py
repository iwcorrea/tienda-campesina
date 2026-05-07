from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.templates import templates
from app.dependencies import get_db
from app.services.actividad_service import obtener_actividades_recientes

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    config = request.state.config
    actividades = obtener_actividades_recientes(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "config": config,
        "actividades": actividades
    })