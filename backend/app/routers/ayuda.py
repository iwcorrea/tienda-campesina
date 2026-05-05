from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ayuda", response_class=HTMLResponse)
def centro_ayuda(request: Request):
    return templates.TemplateResponse("ayuda.html", {"request": request})