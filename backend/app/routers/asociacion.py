from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.asociacion_service import obtener_asociacion_verificada_por_email
from app.viewmodels.asociacion import AsociacionPerfilViewModel
from app.templates import templates

router = APIRouter()


@router.get("/asociacion/{email}", response_class=HTMLResponse)
def perfil_asociacion(request: Request, email: str, db: Session = Depends(get_db)):
    asociacion_orm = obtener_asociacion_verificada_por_email(db, email)
    if not asociacion_orm:
        return RedirectResponse(url="/catalogo", status_code=303)

    asociacion_vm = AsociacionPerfilViewModel.from_orm(asociacion_orm)

    # La plantilla espera "asociacion" y "productos" por separado, los proveemos como el ViewModel
    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "asociacion": {
            "email": asociacion_vm.email,
            "nombre": asociacion_vm.nombre,
            "descripcion": asociacion_vm.descripcion,
            "direccion": asociacion_vm.direccion,
            "telefono": asociacion_vm.telefono,
            "logo_url": asociacion_vm.logo_url,
            "show_whatsapp": asociacion_vm.show_whatsapp,
        },
        "productos": [{
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen": p.imagen,
            "tipo": p.tipo,
            "tipo_precio": p.tipo_precio,
        } for p in asociacion_vm.productos],
    })