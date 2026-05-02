from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import locale

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def format_price(value):
    """Formato colombiano: 1.500,00"""
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

@router.get("/calculadora", response_class=HTMLResponse)
def calculadora_get(request: Request):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("calculadora.html", {"request": request})

@router.post("/calculadora")
def calculadora_post(
    request: Request,
    costos_insumos: str = Form("0"),
    costo_mano_obra: str = Form("0"),
    costo_transporte: str = Form("0"),
    margen_porcentaje: str = Form("20"),
    cantidad_producto: str = Form("1")
):
    if request.session.get("tipo_usuario") != "asociacion":
        return RedirectResponse(url="/auth/login", status_code=303)

    # Normalizar entradas: aceptar coma como decimal y punto como miles
    def parse_num(s):
        # Elimina puntos de miles y convierte coma decimal en punto
        s = s.strip().replace(" ", "")
        if not s:
            return 0.0
        # Si hay coma, asumimos que es decimal
        if "," in s and "." in s:
            # Caso 1.500,00 -> punto es miles, coma decimal
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            # Solo coma decimal
            s = s.replace(",", ".")
        # s ahora es formato americanizado
        try:
            return float(s)
        except ValueError:
            return 0.0

    costos_insumos_n = parse_num(costos_insumos)
    costo_mano_n = parse_num(costo_mano_obra)
    costo_transporte_n = parse_num(costo_transporte)
    margen_pct = parse_num(margen_porcentaje)
    cantidad_p = parse_num(cantidad_producto)

    costo_total = costos_insumos_n + costo_mano_n + costo_transporte_n
    if cantidad_p <= 0:
        cantidad_p = 1.0
    costo_unitario = costo_total / cantidad_p
    precio_sugerido = costo_unitario * (1 + margen_pct / 100)

    resultado = format_price(precio_sugerido)

    return templates.TemplateResponse("calculadora.html", {
        "request": request,
        "resultado": resultado,
        "costos_insumos": costos_insumos,
        "costo_mano_obra": costo_mano_obra,
        "costo_transporte": costo_transporte,
        "margen_porcentaje": margen_porcentaje,
        "cantidad_producto": cantidad_producto
    })