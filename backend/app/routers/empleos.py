import uuid
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Vacante, Aplicacion, Persona
import cloudinary.uploader
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def subir_terminos(file: UploadFile):
    if not file or not file.filename:
        return ""
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="terminos_referencia",
            resource_type="raw",
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public"
        )
        return result.get("secure_url", "")
    except Exception:
        return ""

# ─── BOLSA DE EMPLEO (PÚBLICA) ─────────────────────
@router.get("/bolsa-empleo", response_class=HTMLResponse)
def bolsa_empleo(request: Request, db: Session = Depends(get_db)):
    vacantes = db.query(Vacante).filter(Vacante.fecha_limite >= datetime.datetime.now()).order_by(Vacante.fecha_publicacion.desc()).all()
    return templates.TemplateResponse("bolsa_empleo.html", {"request": request, "vacantes": vacantes})

# ─── DETALLE DE VACANTE ────────────────────────────
@router.get("/bolsa-empleo/{vacante_id}", response_class=HTMLResponse)
def detalle_vacante(request: Request, vacante_id: str, db: Session = Depends(get_db)):
    vacante = db.query(Vacante).filter(Vacante.id == vacante_id).first()
    if not vacante:
        return RedirectResponse(url="/bolsa-empleo", status_code=303)

    persona_actual = None
    if request.session.get("tipo_usuario") == "persona":
        persona_actual = db.query(Persona).filter(Persona.email == request.session["usuario"]).first()

    return templates.TemplateResponse("vacante_detalle.html", {
        "request": request,
        "vacante": vacante,
        "persona": persona_actual
    })

# ─── APLICAR A VACANTE (SOLO PERSONAS) ─────────────
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

    nueva = Aplicacion(vacante_id=vacante_id, persona_email=persona_email, mensaje=mensaje or "")
    db.add(nueva)
    db.commit()
    return RedirectResponse(url=f"/bolsa-empleo/{vacante_id}?aplicado=1", status_code=303)

# ─── PANEL DE VACANTES PARA ASOCIACIÓN ─────────────
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
    salario_convenir: str = Form(None),       # "1" si está marcado
    tipo_contrato: str = Form("termino_fijo"),
    jornada: str = Form("completa"),
    requisitos: str = Form(""),
    fecha_limite: str = Form(...),
    terminos: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    try:
        fecha = datetime.datetime.strptime(fecha_limite, "%Y-%m-%d")
    except ValueError:
        fecha = datetime.datetime.now() + datetime.timedelta(days=30)

    salario_final = 0 if salario_convenir == "1" else salario
    terminos_url = subir_terminos(terminos)

    nueva = Vacante(
        id=str(uuid.uuid4()),
        asociacion_email=email,
        cargo=cargo,
        descripcion=descripcion or "",
        ubicacion=ubicacion or "",
        salario=salario_final,
        tipo_contrato=tipo_contrato,
        jornada=jornada,
        requisitos=requisitos or "",
        fecha_limite=fecha,
        terminos_url=terminos_url
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
        if vacante.terminos_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(vacante.terminos_url, resource_type="raw")
        db.delete(vacante)
        db.commit()
    return RedirectResponse(url="/panel/vacantes", status_code=303)