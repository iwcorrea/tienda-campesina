import time
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.modules.auth.service import (
    validar_contraseña,
    autenticar_usuario,
    registrar_usuario,
    cambiar_password,
)
from app.modules.auth.dependencies import get_db
from app.templates import templates

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    resultado = autenticar_usuario(db, email, password)
    if resultado:
        tipo, nombre, es_admin = resultado
        request.session["usuario"] = email
        request.session["tipo_usuario"] = tipo
        request.session["nombre_usuario"] = nombre
        request.session["last_activity"] = time.time()
        if es_admin:
            request.session["es_admin"] = True
        if tipo == "asociacion":
            return RedirectResponse(url="/dashboard", status_code=303)
        elif tipo == "persona":
            return RedirectResponse(url="/catalogo", status_code=303)
        elif tipo == "transportista":
            return RedirectResponse(url="/perfil-transportista", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Correo o contraseña incorrectos."})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/registro", response_class=HTMLResponse)
def registro_asociacion_form(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

@router.post("/registro")
def registro_asociacion(request: Request, email: str = Form(...), password: str = Form(...), nombre: str = Form(...), descripcion: str = Form(""), direccion: str = Form(""), telefono: str = Form(""), db: Session = Depends(get_db)):
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro.html", {"request": request, "error": msg, "email": email, "nombre": nombre, "descripcion": descripcion, "direccion": direccion, "telefono": telefono})
    resultado = registrar_usuario(db, "asociacion", {"email": email, "password": password, "nombre": nombre, "descripcion": descripcion, "direccion": direccion, "telefono": telefono})
    if resultado is not True:
        return templates.TemplateResponse("registro.html", {"request": request, "error": resultado, "email": email, "nombre": nombre, "descripcion": descripcion, "direccion": direccion, "telefono": telefono})
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)

@router.get("/registro-persona", response_class=HTMLResponse)
def registro_persona_form(request: Request):
    return templates.TemplateResponse("registro_persona.html", {"request": request})

@router.post("/registro-persona")
def registro_persona(request: Request, email: str = Form(...), password: str = Form(...), nombre: str = Form(...), telefono: str = Form(""), db: Session = Depends(get_db)):
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro_persona.html", {"request": request, "error": msg, "email": email, "nombre": nombre, "telefono": telefono})
    resultado = registrar_usuario(db, "persona", {"email": email, "password": password, "nombre": nombre, "telefono": telefono})
    if resultado is not True:
        return templates.TemplateResponse("registro_persona.html", {"request": request, "error": resultado, "email": email, "nombre": nombre, "telefono": telefono})
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)

@router.get("/registro-transportista", response_class=HTMLResponse)
def registro_transportista_form(request: Request):
    return templates.TemplateResponse("registro_transportista.html", {"request": request})

@router.post("/registro-transportista")
def registro_transportista(request: Request, email: str = Form(...), password: str = Form(...), nombre: str = Form(...), telefono: str = Form(""), tipo_vehiculo: str = Form("camioneta"), capacidad: str = Form("500 kg"), zona_cobertura: str = Form("Local"), tarifa_base: int = Form(5000), costo_km: int = Form(1500), db: Session = Depends(get_db)):
    valida, msg = validar_contraseña(password)
    if not valida:
        return templates.TemplateResponse("registro_transportista.html", {"request": request, "error": msg, "email": email, "nombre": nombre, "telefono": telefono})
    resultado = registrar_usuario(db, "transportista", {"email": email, "password": password, "nombre": nombre, "telefono": telefono, "tipo_vehiculo": tipo_vehiculo, "capacidad": capacidad, "zona_cobertura": zona_cobertura, "tarifa_base": tarifa_base, "costo_km": costo_km})
    if resultado is not True:
        return templates.TemplateResponse("registro_transportista.html", {"request": request, "error": resultado, "email": email, "nombre": nombre, "telefono": telefono})
    return RedirectResponse(url="/auth/login?registro=ok", status_code=303)

@router.get("/cambiar-password", response_class=HTMLResponse)
def cambiar_password_form(request: Request):
    if not request.session.get("usuario"):
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("cambiar_password.html", {"request": request})

@router.post("/cambiar-password")
def cambiar_password_post(request: Request, password_actual: str = Form(...), password_nueva: str = Form(...), password_confirmacion: str = Form(...), db: Session = Depends(get_db)):
    email = request.session.get("usuario")
    if not email:
        return RedirectResponse(url="/auth/login", status_code=303)
    if password_nueva != password_confirmacion:
        return templates.TemplateResponse("cambiar_password.html", {"request": request, "error": "Las contraseñas no coinciden."})
    valida, msg = validar_contraseña(password_nueva)
    if not valida:
        return templates.TemplateResponse("cambiar_password.html", {"request": request, "error": msg})
    error = cambiar_password(db, email, password_actual, password_nueva)
    if error:
        return templates.TemplateResponse("cambiar_password.html", {"request": request, "error": error})
    return RedirectResponse(url="/auth/login?cambio=ok", status_code=303)