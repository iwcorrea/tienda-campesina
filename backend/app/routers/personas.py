from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates
from app.models import Persona  # Ajusta si es diferente

router = APIRouter()

@router.get("/personas", response_class=HTMLResponse)
def listar_personas(request: Request, db: Session = Depends(get_db)):
    # Ejemplo: listar personas (si aplica)
    return templates.TemplateResponse("personas.html", {"request": request})

@router.get("/personas/{email}", response_class=HTMLResponse)
def detalle_persona(request: Request, email: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.email == email).first()
    if not persona:
        return RedirectResponse(url="/personas", status_code=303)
    return templates.TemplateResponse("persona_detalle.html", {"request": request, "persona": persona})