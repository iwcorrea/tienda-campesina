from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    config = request.state.config
    return templates.TemplateResponse("index.html", {"request": request, "config": config})