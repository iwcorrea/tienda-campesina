from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates
from app.models import Persona, ValoracionComprador

router = APIRouter()

@router.get("/perfil", response_class=HTMLResponse)
def perfil(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    tipo = current_user.get("tipo")
    if tipo == "transportista":
        return RedirectResponse(url="/perfil-transportista", status_code=303)
    
    if tipo == "persona":
        persona = db.query(Persona).filter(Persona.email == current_user["email"]).first()
        valoraciones = db.query(ValoracionComprador).filter(ValoracionComprador.comprador_email == current_user["email"]).all()
        return templates.TemplateResponse("perfil_persona.html", {
            "request": request, 
            "persona": persona or current_user,
            "valoraciones": valoraciones
        })
    
    return RedirectResponse(url="/panel", status_code=303)