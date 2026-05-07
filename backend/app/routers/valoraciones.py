from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates

router = APIRouter()

@router.get("/valoraciones", response_class=HTMLResponse)
def valoraciones(request: Request, db: Session = Depends(get_db)):
    # Aquí puedes listar valoraciones o redirigir según la lógica original.
    # Si no hay lógica, simplemente retornamos una plantilla.
    return templates.TemplateResponse("valoraciones.html", {"request": request})