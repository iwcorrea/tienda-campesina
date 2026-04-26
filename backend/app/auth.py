from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

router = APIRouter()

# 🔥 FORMULARIO LOGIN
@router.get("/login", response_class=HTMLResponse)
def login_form():
    return """
    <h2>Login</h2>
    <form method="post">
        <input name="email" placeholder="Email"/><br>
        <input name="password" type="password" placeholder="Password"/><br>
        <button type="submit">Ingresar</button>
    </form>
    <a href="/menu">Volver</a>
    """

# 🔥 LOGIN
@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    
    if email != "admin@test.com" or password != "1234":
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    request.session["user_id"] = 1

    return RedirectResponse("/auth/dashboard", status_code=303)


# 🔥 DASHBOARD
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="No autenticado")

    return """
    <h2>Bienvenido</h2>
    <p>Login correcto</p>
    <a href="/menu">Ir al menú</a>
    """


# 🔥 REGISTRO (TEMPORAL)
@router.get("/registro", response_class=HTMLResponse)
def registro():
    return """
    <h2>Registro</h2>
    <p>Próximamente conexión con base de datos</p>
    <a href="/menu">Volver</a>
    """