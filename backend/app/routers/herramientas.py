from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates import templates
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/herramientas/contrato", response_class=HTMLResponse)
def contrato(request: Request):
    return templates.TemplateResponse("contrato.html", {"request": request})

@router.get("/herramientas", response_class=HTMLResponse)
def herramientas(request: Request):
    return templates.TemplateResponse("herramientas.html", {"request": request})