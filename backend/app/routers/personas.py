from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Persona, Aplicacion
import cloudinary.uploader

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/perfil", response_class=HTMLResponse)
def perfil_persona(request: Request, db: Session = Depends(get_db)):
    if request.session.get("tipo_usuario") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    persona = db.query(Persona).filter(Persona.email == email).first()
    if not persona:
        return RedirectResponse(url="/auth/login", status_code=303)

    aplicaciones = db.query(Aplicacion).filter(Aplicacion.persona_email == email).all()
    apps_info = []
    for a in aplicaciones:
        apps_info.append({
            "cargo": a.vacante.cargo if a.vacante else "Cargo desconocido",
            "asociacion": a.vacante.asociacion.nombre if a.vacante and a.vacante.asociacion else "",
            "fecha": a.fecha_aplicacion.strftime("%d/%m/%Y") if a.fecha_aplicacion else ""
        })

    return templates.TemplateResponse("perfil_persona.html", {
        "request": request,
        "persona": persona,
        "aplicaciones": apps_info
    })

@router.post("/perfil/actualizar")
def actualizar_perfil_persona(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(None),
    hoja_vida: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if request.session.get("tipo_usuario") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)
    email = request.session["usuario"]
    persona = db.query(Persona).filter(Persona.email == email).first()
    if not persona:
        return RedirectResponse(url="/auth/login", status_code=303)

    if hoja_vida and hoja_vida.filename:
        if persona.hoja_vida_url:
            from app.main import delete_cloudinary_asset
            delete_cloudinary_asset(persona.hoja_vida_url, resource_type="raw")
        try:
            result = cloudinary.uploader.upload(
                hoja_vida.file,
                folder="hojas_vida",
                resource_type="raw",
                filename=hoja_vida.filename,
                use_filename=True,
                unique_filename=True,
                access_mode="public"
            )
            persona.hoja_vida_url = result.get("secure_url", "")
        except Exception:
            pass

    persona.nombre = nombre
    persona.telefono = telefono or ""
    db.commit()
    request.session["nombre_usuario"] = persona.nombre
    return RedirectResponse(url="/perfil", status_code=303)