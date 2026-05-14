import uuid
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion, Persona, Transportista
from app.templates import templates
import bcrypt

router = APIRouter()


# ─── VALIDADOR DE CONTRASEÑA ──────────────────────
def validar_contraseña(password: str):
    """
    Valida que la contraseña cumpla con los lineamientos de Google:
    - Mínimo 12 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un símbolo especial (ASCII)
    Retorna (True, "") si es válida, o (False, mensaje) si no.
    """
    if len(password) < 12:
        return False, "La contraseña debe tener al menos 12 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe incluir al menos una letra mayúscula."
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe incluir al menos una letra minúscula."
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe incluir al menos un número."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
        return False, "La contraseña debe incluir al menos un símbolo especial (ej: ! @ # $ %)."
    return True, ""


# ─── LOGIN ────────────────────────────────────────
@router.get("/auth/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/auth/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Intentar autenticar como asociación
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()
    if asociacion and bcrypt.checkpw(password.encode(), asociacion.hashed_password.encode()):
        request.session["usuario"] = email
        request.session["tipo_usuario"] = "asociacion"
        request.session["nombre_usuario"] = asociacion.nombre or email
        if email == "admin@example.com":           # ajusta según tu lógica de admin
            request.session["es_admin"] = True
        return RedirectResponse(url="/dashboard", status_code=303)

    # Intentar como persona
    persona = db.query(Persona).filter(Persona.email == email).first()
    if persona and bcrypt.checkpw(password.encode(), persona.hashed_password.encode()):
        request.session["usuario"] = email
        request.session["tipo_usuario"] = "persona"
        request.session["nombre_usuario"] = persona.nombre or email
        return RedirectResponse(url="/catalogo", status_code=303)

    # Intentar como transportista
    transportista = db.query(Transportista).filter(Transportista.email == email).first()
    if transportista and bcrypt.checkpw(password.encode(), transportista.hashed_password.encode()):
        request.session["usuario"] = email
        request.session["tipo_usuario"] = "transportista"
        request.session["nombre_usuario"] = transportista.nombre or email
        return RedirectResponse(url="/perfil-transportista", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Correo o contraseña incorrectos."
    })


# ─── LOGOUT ───────────────────────────────────────
@router.get("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ─── REGISTRO ASOCIACIÓN ──────────────────────────
@router.get("/auth/registro", response_class=HTMLResponse)
def registro_asociacion_form(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


@router.post("/auth/registro")
def registro_asociacion(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    descripcion: str = Form(""),
    direccion: str = Form(""),
    telefono: str = Form(""),
    db: Session = Depends(get_db)
):
    # Validar contraseña segura
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro.html", {
            "request": request,
            "error": msg,
            "email": email,
            "nombre": nombre,
            "descripcion": descripcion,
            "direccion": direccion,
            "telefono": telefono,
        })

    existe = db.query(Asociacion).filter(Asociacion.email == email).first()
    if existe:
        return templates.TemplateResponse("registro.html", {
            "request": request,
            "error": "Ya existe una asociación con ese correo.",
            "email": email,
            "nombre": nombre,
            "descripcion": descripcion,
            "direccion": direccion,
            "telefono": telefono,
        })

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    nueva = Asociacion(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed,
        nombre=nombre,
        descripcion=descripcion,
        direccion=direccion,
        telefono=telefono,
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)


# ─── REGISTRO PERSONA ─────────────────────────────
@router.get("/auth/registro-persona", response_class=HTMLResponse)
def registro_persona_form(request: Request):
    return templates.TemplateResponse("registro_persona.html", {"request": request})


@router.post("/auth/registro-persona")
def registro_persona(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    telefono: str = Form(""),
    db: Session = Depends(get_db)
):
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro_persona.html", {
            "request": request,
            "error": msg,
            "email": email,
            "nombre": nombre,
            "telefono": telefono,
        })

    existe = db.query(Persona).filter(Persona.email == email).first()
    if existe:
        return templates.TemplateResponse("registro_persona.html", {
            "request": request,
            "error": "Ya existe una persona con ese correo.",
            "email": email,
            "nombre": nombre,
            "telefono": telefono,
        })

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    nueva = Persona(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed,
        nombre=nombre,
        telefono=telefono,
    )
    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)


# ─── REGISTRO TRANSPORTISTA ───────────────────────
@router.get("/auth/registro-transportista", response_class=HTMLResponse)
def registro_transportista_form(request: Request):
    return templates.TemplateResponse("registro_transportista.html", {"request": request})


@router.post("/auth/registro-transportista")
def registro_transportista(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    telefono: str = Form(""),
    tipo_vehiculo: str = Form("camioneta"),
    capacidad: str = Form("500 kg"),
    zona_cobertura: str = Form("Local"),
    tarifa_base: int = Form(5000),
    costo_km: int = Form(1500),
    db: Session = Depends(get_db)
):
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro_transportista.html", {
            "request": request,
            "error": msg,
            "email": email,
            "nombre": nombre,
            "telefono": telefono,
        })

    existe = db.query(Transportista).filter(Transportista.email == email).first()
    if existe:
        return templates.TemplateResponse("registro_transportista.html", {
            "request": request,
            "error": "Ya existe un transportista con ese correo.",
            "email": email,
            "nombre": nombre,
            "telefono": telefono,
        })

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    nuevo = Transportista(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed,
        nombre=nombre,
        telefono=telefono,
        tipo_vehiculo=tipo_vehiculo,
        capacidad=capacidad,
        zona_cobertura=zona_cobertura,
        tarifa_base=tarifa_base,
        costo_km=costo_km,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)


# ─── CAMBIAR CONTRASEÑA ───────────────────────────
@router.get("/auth/cambiar-password", response_class=HTMLResponse)
def cambiar_password_form(request: Request):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("cambiar_password.html", {"request": request})


@router.post("/auth/cambiar-password")
def cambiar_password(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    password_confirmacion: str = Form(...),
    db: Session = Depends(get_db)
):
    email = request.session.get("usuario")
    if not email:
        return RedirectResponse(url="/auth/login", status_code=303)

    if password_nueva != password_confirmacion:
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "error": "Las contraseñas no coinciden."
        })

    valida, msg = validar_contraseña(password_nueva)
    if not valida:
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "error": msg,
        })

    # Buscar el usuario en los tres tipos
    usuario = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not usuario:
        usuario = db.query(Persona).filter(Persona.email == email).first()
    if not usuario:
        usuario = db.query(Transportista).filter(Transportista.email == email).first()

    if not usuario:
        return RedirectResponse(url="/auth/login", status_code=303)

    if not bcrypt.checkpw(password_actual.encode(), usuario.hashed_password.encode()):
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "error": "La contraseña actual es incorrecta."
        })

    usuario.hashed_password = bcrypt.hashpw(password_nueva.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return RedirectResponse(url="/auth/login?cambio=ok", status_code=303)