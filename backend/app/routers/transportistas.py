from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transportista

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/perfil-transportista", response_class=HTMLResponse)
def perfil_transportista(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    transportista = db.query(Transportista).filter(Transportista.email == email).first()
    if not transportista:
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("perfil_transportista.html", {
        "request": request,
        "transportista": transportista
    })

@router.post("/perfil-transportista/actualizar")
def actualizar_perfil_transportista(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(None),
    tipo_vehiculo: str = Form(...),
    capacidad: str = Form(...),
    zona_cobertura: str = Form(...),
    tarifa_base: int = Form(...),
    costo_km: int = Form(...),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    t = db.query(Transportista).filter(Transportista.email == email).first()
    if not t:
        return RedirectResponse(url="/auth/login", status_code=303)
    t.nombre = nombre
    t.telefono = telefono or ""
    t.tipo_vehiculo = tipo_vehiculo
    t.capacidad = capacidad
    t.zona_cobertura = zona_cobertura
    t.tarifa_base = tarifa_base
    t.costo_km = costo_km
    db.commit()
    return RedirectResponse(url="/perfil-transportista", status_code=303)