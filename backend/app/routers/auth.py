from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..auth import create_token, hash_password, verify_password
from ..database import get_db
from ..models import Asociacion

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="backend/app/templates")


@router.get("/registro")
def registro_form(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


@router.post("/registro")
def registro_post(
    request: Request,
    email: str = Form(...),
    nombre_asociacion: str = Form(...),
    password: str = Form(...),
    descripcion: str = Form(None),
    direccion: str = Form(None),
    telefono: str = Form(None),
    db: Session = Depends(get_db),
):
    existente = db.query(Asociacion).filter(Asociacion.email == email).first()
    if existente:
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "El email ya esta registrado."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    asociacion = Asociacion(
        email=email,
        nombre_asociacion=nombre_asociacion,
        descripcion=descripcion,
        direccion=direccion,
        telefono=telefono,
        hashed_password=hash_password(password),
    )
    db.add(asociacion)
    db.commit()

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(Asociacion).filter(Asociacion.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales invalidas."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_token({"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
