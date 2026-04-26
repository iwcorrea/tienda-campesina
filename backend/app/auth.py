from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/login")
def login_form():
    return """
    <form method="post">
        <input name="email"/>
        <input name="password" type="password"/>
        <button type="submit">Login</button>
    </form>
    """

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    
    if email != "admin@test.com" or password != "1234":
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    request.session["user_id"] = 1

    return RedirectResponse("/auth/dashboard", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="No autenticado")

    return {"message": "Login correcto"}