from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asociacion
from app.utils import verify_password

router = APIRouter()

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    asociacion = db.query(Asociacion).filter(Asociacion.email == email).first()

    if not asociacion or not verify_password(password, asociacion.password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    # 🔑 Guardar sesión
    request.session["user_id"] = int(asociacion.id)

    return RedirectResponse(
        url="/asociaciones/dashboard",
        status_code=303
    )