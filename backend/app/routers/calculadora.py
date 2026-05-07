from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates import templates

router = APIRouter()

@router.get("/calculadora", response_class=HTMLResponse)
def calculadora(request: Request):
    return templates.TemplateResponse("calculadora.html", {"request": request})