from fastapi import APIRouter, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.services.empleo_service import (
    listar_vacantes_publicas,
    obtener_vacante_por_id,
    obtener_persona_actual,
    aplicar_a_vacante,
    listar_vacantes_por_asociacion,
    crear_vacante,
    eliminar_vacante,
    obtener_postulantes,
    seleccionar_candidato,
)
from app.modules.notifications.service import crear_notificacion
from app.viewmodels.empleo import VacanteViewModel
from app.templates import templates

router = APIRouter()


@router.get("/bolsa-empleo", response_class=HTMLResponse)
def bolsa_empleo(request: Request, db: Session = Depends(get_db)):
    vacantes_orm = listar_vacantes_publicas(db)
    vacantes_vm = [VacanteViewModel.from_orm(v) for v in vacantes_orm]
    return templates.TemplateResponse("bolsa_empleo.html", {
        "request": request,
        "vacantes": vacantes_vm,
    })


@router.get("/bolsa-empleo/{vacante_id}", response_class=HTMLResponse)
def detalle_vacante(
    request: Request,
    vacante_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    vacante = obtener_vacante_por_id(db, vacante_id)
    if not vacante:
        return RedirectResponse(url="/bolsa-empleo", status_code=303)

    persona_actual = None
    if current_user and current_user.get("tipo") == "persona":
        persona_actual = obtener_persona_actual(db, current_user["email"])

    aplicado = False
    if persona_actual:
        from app.models import Aplicacion
        existente = db.query(Aplicacion).filter(
            Aplicacion.vacante_id == vacante_id,
            Aplicacion.persona_email == persona_actual.email
        ).first()
        aplicado = existente is not None

    return templates.TemplateResponse("vacante_detalle.html", {
        "request": request,
        "vacante": vacante,
        "persona": persona_actual,
        "aplicado": aplicado,
    })


@router.post("/aplicar/{vacante_id}")
def aplicar_vacante(
    request: Request,
    vacante_id: str,
    mensaje: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "persona":
        return RedirectResponse(url="/auth/login", status_code=303)

    aplicar_a_vacante(db, vacante_id, current_user["email"], mensaje)
    return RedirectResponse(url=f"/bolsa-empleo/{vacante_id}?aplicado=1", status_code=303)


@router.get("/panel/vacantes", response_class=HTMLResponse)
def panel_vacantes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    vacantes_orm = listar_vacantes_por_asociacion(db, current_user["email"])
    vacantes_vm = [VacanteViewModel.from_orm(v) for v in vacantes_orm]
    return templates.TemplateResponse("panel_vacantes.html", {
        "request": request,
        "vacantes": vacantes_vm,
    })


@router.post("/panel/vacantes/crear")
def crear_vacante_post(
    request: Request,
    cargo: str = Form(...),
    descripcion: str = Form(None),
    ubicacion: str = Form(None),
    salario: int = Form(0),
    salario_convenir: str = Form(None),
    tipo_contrato: str = Form("termino_fijo"),
    jornada: str = Form("completa"),
    requisitos: str = Form(""),
    fecha_limite: str = Form(...),
    terminos: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    crear_vacante(
        db,
        asociacion_email=current_user["email"],
        cargo=cargo,
        descripcion=descripcion,
        ubicacion=ubicacion,
        salario=salario,
        salario_convenir=salario_convenir,
        tipo_contrato=tipo_contrato,
        jornada=jornada,
        requisitos=requisitos,
        fecha_limite_str=fecha_limite,
        terminos=terminos,
    )
    return RedirectResponse(url="/panel/vacantes", status_code=303)


@router.get("/panel/vacantes/{vacante_id}/postulantes", response_class=HTMLResponse)
def ver_postulantes(
    request: Request,
    vacante_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    vacante, postulantes = obtener_postulantes(db, vacante_id, current_user["email"])
    if not vacante:
        return RedirectResponse(url="/panel/vacantes", status_code=303)

    return templates.TemplateResponse("postulantes.html", {
        "request": request,
        "vacante": vacante,
        "postulantes": postulantes,
    })


@router.post("/panel/vacantes/{vacante_id}/seleccionar")
def seleccionar_candidato_post(
    request: Request,
    vacante_id: str,
    persona_email: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    vacante = seleccionar_candidato(db, vacante_id, current_user["email"], persona_email)
    if not vacante:
        return RedirectResponse(url="/panel/vacantes?error=seleccion", status_code=303)

    # Notificar a la persona seleccionada
    crear_notificacion(
        db,
        destinatario_email=persona_email,
        remitente_email=current_user["email"],
        texto=f"Has sido seleccionado para el cargo '{vacante.cargo}'. Revisa tu bandeja de mensajes.",
    )

    # Notificar a la asociación (confirmación)
    crear_notificacion(
        db,
        destinatario_email=current_user["email"],
        remitente_email=current_user["email"],
        texto=f"Seleccionaste a {persona_email} para la vacante '{vacante.cargo}'. Documento generado.",
    )

    return RedirectResponse(url="/panel/vacantes?seleccionado=1", status_code=303)


@router.post("/panel/vacantes/eliminar/{vacante_id}")
def eliminar_vacante_post(
    request: Request,
    vacante_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user or current_user.get("tipo") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    eliminar_vacante(db, vacante_id, current_user["email"])
    return RedirectResponse(url="/panel/vacantes", status_code=303)