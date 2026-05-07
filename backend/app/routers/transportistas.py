from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.services.transportista_service import (
    obtener_transportista_por_email,
    actualizar_perfil_transportista,
)
from app.viewmodels.transportista import TransportistaViewModel
from app.templates import templates
import cloudinary.uploader


router = APIRouter()


def upload_file_cloudinary(file: UploadFile, folder: str, raw: bool = False):
    if not file or not file.filename:
        return ""
    try:
        kwargs = dict(
            folder=folder,
            filename=file.filename,
            use_filename=True,
            unique_filename=True,
            access_mode="public",
        )
        if raw:
            kwargs["resource_type"] = "raw"
        result = cloudinary.uploader.upload(file.file, **kwargs)
        return result.get("secure_url", "")
    except Exception:
        return ""


@router.get("/perfil-transportista", response_class=HTMLResponse)
def perfil_transportista(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)

    transportista = obtener_transportista_por_email(db, current_user["email"])
    if not transportista:
        return RedirectResponse(url="/auth/login", status_code=303)

    transportista_vm = TransportistaViewModel.from_orm(transportista)
    return templates.TemplateResponse("perfil_transportista.html", {
        "request": request,
        "transportista": transportista_vm,
    })


@router.post("/perfil-transportista/actualizar")
def actualizar_perfil_transportista_post(
    request: Request,
    nombre: str = Form(...),
    telefono: str = Form(None),
    tipo_vehiculo: str = Form(...),
    capacidad: str = Form(...),
    zona_cobertura: str = Form(...),
    tarifa_base: int = Form(...),
    costo_km: int = Form(...),
    documento: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "transportista":
        return RedirectResponse(url="/auth/login", status_code=303)

    documento_url = upload_file_cloudinary(documento, "documentos_transportistas", raw=True)

    resultado = actualizar_perfil_transportista(
        db,
        email=current_user["email"],
        nombre=nombre,
        telefono=telefono,
        tipo_vehiculo=tipo_vehiculo,
        capacidad=capacidad,
        zona_cobertura=zona_cobertura,
        tarifa_base=tarifa_base,
        costo_km=costo_km,
        documento_url=documento_url if documento_url else None,
    )
    if not resultado:
        return RedirectResponse(url="/auth/login", status_code=303)

    return RedirectResponse(url="/perfil-transportista", status_code=303)