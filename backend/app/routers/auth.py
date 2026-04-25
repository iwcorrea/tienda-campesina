from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import hash_password, verify_password, create_token, obtener_usuario_actual
from ..dependencies import templates

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/registro", response_class=HTMLResponse)
def registro_form(request: Request):
    template = templates.env.get_template("registro.html")
    return HTMLResponse(content=template.render({"request": request}))

@router.post("/registro", response_class=HTMLResponse)
def registro(
    request: Request,
    email: str = Form(...),
    nombre_asociacion: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validar longitud de contraseña (bcrypt max 72 bytes)
    if len(password.encode('utf-8')) > 72:
        template = templates.env.get_template("registro.html")
        return HTMLResponse(
            content=template.render({"request": request, "error": "La contraseña no puede superar los 72 caracteres."}),
            status_code=400
        )
    
    usuario_existente = db.query(models.Asociacion).filter(models.Asociacion.email == email).first()
    if usuario_existente:
        template = templates.env.get_template("registro.html")
        return HTMLResponse(
            content=template.render({"request": request, "error": "El email ya está registrado"}),
            status_code=400
        )
    
    hashed = hash_password(password)
    nueva_asociacion = models.Asociacion(
        email=email,
        nombre_asociacion=nombre_asociacion,
        descripcion=descripcion,
        direccion=direccion,
        telefono=telefono,
        hashed_password=hashed
    )
    db.add(nueva_asociacion)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    template = templates.env.get_template("login.html")
    return HTMLResponse(content=template.render({"request": request}))

@router.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validar longitud de contraseña para evitar errores internos
    if len(password.encode('utf-8')) > 72:
        template = templates.env.get_template("login.html")
        return HTMLResponse(
            content=template.render({"request": request, "error": "La contraseña no puede superar los 72 caracteres."}),
            status_code=400
        )
    
    asociacion = db.query(models.Asociacion).filter(models.Asociacion.email == email).first()
    if not asociacion or not verify_password(password, asociacion.hashed_password):
        template = templates.env.get_template("login.html")
        return HTMLResponse(
            content=template.render({"request": request, "error": "Credenciales inválidas"}),
            status_code=401
        )
    
    token = create_token({"sub": str(asociacion.id)})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/", status_code=303)