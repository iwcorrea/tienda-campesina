from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/calculadora", response_class=HTMLResponse)
def calculadora_get(request: Request):
    return templates.TemplateResponse("calculadora.html", {"request": request})

@router.post("/calculadora")
def calculadora_post(
    request: Request,
    costos_insumos: float = Form(0.0),
    costo_mano_obra: float = Form(0.0),
    costo_transporte: float = Form(0.0),
    margen_porcentaje: float = Form(20.0),
    cantidad_producto: float = Form(1.0)
):
    costo_total = costos_insumos + costo_mano_obra + costo_transporte
    if cantidad_producto <= 0:
        cantidad_producto = 1.0
    costo_unitario = costo_total / cantidad_producto
    precio_sugerido = costo_unitario * (1 + margen_porcentaje / 100)
    resultado = round(precio_sugerido, 2)
    return templates.TemplateResponse("calculadora.html", {
        "request": request,
        "resultado": resultado,
        "costos_insumos": costos_insumos,
        "costo_mano_obra": costo_mano_obra,
        "costo_transporte": costo_transporte,
        "margen_porcentaje": margen_porcentaje,
        "cantidad_producto": cantidad_producto
    })