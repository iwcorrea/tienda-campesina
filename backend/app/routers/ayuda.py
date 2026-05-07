from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates import templates

router = APIRouter()

@router.get("/ayuda", response_class=HTMLResponse)
def ayuda(request: Request):
    return templates.TemplateResponse("ayuda.html", {"request": request})