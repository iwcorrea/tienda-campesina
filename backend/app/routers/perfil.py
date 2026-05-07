from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.templates import templates

router = APIRouter()

@router.get("/perfil", response_class=HTMLResponse)
def perfil(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=303)
    # Lógica específica según tipo de usuario:
    # Si es persona, muestra su perfil; si es transportista, redirige al perfil transportista.
    tipo = current_user.get("tipo")
    if tipo == "transportista":
        return RedirectResponse(url="/perfil-transportista", status_code=303)
    if tipo == "persona":
        # Aquí puedes cargar datos de la persona si es necesario
        return templates.TemplateResponse("perfil_persona.html", {"request": request, "usuario": current_user})
    # Para otros casos (asociación) redirigir al catálogo o a su panel
    return RedirectResponse(url="/panel", status_code=303)