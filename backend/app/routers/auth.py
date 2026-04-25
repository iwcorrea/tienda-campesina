from fastapi import APIRouter, Request, Depends, HTTPException, status, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import hash_password, verify_password, create_token
from ..dependencies import templates

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/registro", response_class=HTMLResponse)
def registro_form(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})

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
    usuario_existente = db.query(models.Asociacion).filter(models.Asociacion.email == email).first()
    if usuario_existente:
        return templates.TemplateResponse("registro.html", {"request": request, "error": "El email ya está registrado"})
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
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    asociacion = db.query(models.Asociacion).filter(models.Asociacion.email == email).first()
    if not asociacion or not verify_password(password, asociacion.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales inválidas"})
    token = create_token({"sub": str(asociacion.id)})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)  # 7 días
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/", status_code=303)