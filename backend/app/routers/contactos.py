from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.contacto_service import agregar_contacto, eliminar_contacto, listar_contactos, obtener_info_contacto
from app.templates import templates

router = APIRouter(prefix="/contactos", tags=["contactos"])

@router.get("/", response_class=HTMLResponse)
def panel_contactos(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    contactos_orm = listar_contactos(db, current_user["email"])
    contactos = []
    for c in contactos_orm:
        info = obtener_info_contacto(db, c.contacto_email)
        contactos.append({
            "email": c.contacto_email,
            "nombre": info["nombre"] if info else c.contacto_email,
            "tipo": info["tipo"] if info else "desconocido",
            "logo": info.get("logo") if info else None,
            "relacion": c.tipo_relacion
        })
    return templates.TemplateResponse("contactos.html", {"request": request, "contactos": contactos})

@router.post("/agregar")
def agregar(request: Request, contacto_email: str = Form(...), tipo_relacion: str = Form("contacto"), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    agregar_contacto(db, current_user["email"], contacto_email, tipo_relacion)
    return RedirectResponse(url="/contactos", status_code=303)

@router.post("/eliminar")
def eliminar(request: Request, contacto_email: str = Form(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    eliminar_contacto(db, current_user["email"], contacto_email)
    return RedirectResponse(url="/contactos", status_code=303)