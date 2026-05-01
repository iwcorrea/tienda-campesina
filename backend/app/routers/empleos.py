import uuid
from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Vacante, Aplicacion
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/bolsa-empleo", response_class=HTMLResponse)
def bolsa_empleo(request: Request, db: Session = Depends(get_db)):
    vacantes = db.query(Vacante).filter(Vacante.fecha_limite >= datetime.datetime.now()).order_by(Vacante.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("bolsa_empleo.html", {"request": request, "vacantes": vacantes})

@router.get("/bolsa-empleo/{vacante_id}", response_class=HTMLResponse)
def detalle_vacante(request: Request, vacante_id: str, db: Session = Depends(get_db)):
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id).first()
    if not vacante:
        return RedirectResponse(url="/bolsa-empleo", status_code=303)
    return templates.TemplateResponse("vacante_detalle.html", {"request": request, "vacante": vacante})

@router.post("/aplicar/{vacante_id}")
def aplicar_vacante(
    request: Request,
    vacante_id: str,
    mensaje: str = Form(None),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)
    persona_email = request.session["usuario"]

    existente = db.query(Aplicacion).filter(
        Aplicacion.vacante_id == vacante_id,
        Aplicacion.persona_email == persona_email
    ).first()
    if existente:
        return RedirectResponse(url="/bolsa-empleo", status_code=303)

    nueva = Aplicacion(
        vacante_id=vacante_id,
        persona_email=persona_email,
        mensaje=mensaje or ""
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/perfil", status_code=303)

@router.get("/panel/vacantes", response_class=HTMLResponse)
def panel_vacantes(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    vacantes = db.query(Vacante).filter(Vacante.asociacion_email == email).order_by(Vacante.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("panel_vacantes.html", {"request": request, "vacantes": vacantes})

@router.post("/panel/vacantes/crear")
def crear_vacante(
    request: Request,
    cargo: str = Form(...),
    descripcion: str = Form(None),
    ubicacion: str = Form(None),
    salario: int = Form(0),
    fecha_limite: str = Form(...),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    try:
        fecha = datetime.datetime.strptime(fecha_limite, "%Y-%m-%d")
    except ValueError:
        fecha = datetime.datetime.now() + datetime.timedelta(days=30)

    nueva = Vacante(
        id=str(uuid.uuid4()),
        asociacion_email=email,
        cargo=cargo,
        descripcion=descripcion or "",
        ubicacion=ubicacion or "",
        salario=salario,
        fecha_limite=fecha
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/panel/vacantes", status_code=303)

@router.get("/panel/vacantes/{vacante_id}/postulantes", response_class=HTMLResponse)
def ver_postulantes(request: Request, vacante_id: str, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id, Vacante.asociacion_email == email).first()
    if not vacante:
        return RedirectResponse(url="/panel/vacantes", status_code=303)
    aplicaciones = db.query(Aplicacion).filter(Aplicacion.vacante_id == vacante_id).all()
    postulantes = []
    for a in aplicaciones:
        persona = a.persona
        postulantes.append({
            "nombre": persona.nombre if persona else "Desconocido",
            "email": persona.email if persona else "",
            "telefono": persona.telefono if persona else "",
            "hoja_vida_url": persona.hoja_vida_url if persona else "",
            "mensaje": a.mensaje,
            "fecha": a.fecha_aplicacion.strftime("%d/%m/%Y") if a.fecha_aplicacion else ""
        })
    return templates.TemplateResponse("postulantes.html", {"request": request, "vacante": vacante, "postulantes": postulantes})

@router.post("/panel/vacantes/eliminar/{vacante_id}")
def eliminar_vacante(request: Request, vacante_id: str, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id, Vacante.asociacion_email == email).first()
    if vacante:
        db.delete(vacante)
        db.commit()
    return RedirectResponse(url="/panel/vacantes", status_code=303)