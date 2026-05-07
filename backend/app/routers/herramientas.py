from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates import templates

router = APIRouter()

@router.get("/herramientas", response_class=HTMLResponse)
def listar_herramientas(request: Request):
    return templates.TemplateResponse("herramientas.html", {"request": request})

@router.get("/herramientas/contrato", response_class=HTMLResponse)
def contrato(request: Request):
    return templates.TemplateResponse("generar_contrato.html", {"request": request})