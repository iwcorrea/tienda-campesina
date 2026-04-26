from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os

from backend.app.auth import router as auth_router

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=True,
)

app.include_router(auth_router, prefix="/auth")

@app.get("/")
def home():
    return {"status": "ok"}