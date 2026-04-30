import uuid
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Valoracion

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/valorar/{producto_id}")
def valorar_producto(
    request: Request,
    producto_id: str,
    estrellas: int = Form(...),
    comentario: str = Form(None),
    db: Session = Depends(get_db)
):
    if "usuario" not in request.session:
        return RedirectResponse(url="/auth/login", status_code=303)
    if estrellas < 1 or estrellas > 5:
        return RedirectResponse(url="/catalogo", status_code=303)
    email = request.session["usuario"]
    val = Valoracion(
        id=str(uuid.uuid4()),
        producto_id=producto_id,
        estrellas=estrellas,
        comentario=comentario or "",
        email_usuario=email
    )
    db.add(val)
    db.commit()
    return RedirectResponse(url="/catalogo", status_code=303)