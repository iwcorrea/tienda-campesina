from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})