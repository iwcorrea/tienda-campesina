from fastapi import APIRouter, Request, Depends, HTTPException, status, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..auth import hash_password, verify_password, create_token, get_current_user
from ..dependencies import templates

router = APIRouter(prefix="/auth", tags=["auth"])

# Aquí van tus endpoints: /registro, /login, /logout
# Asegúrate de que `get_current_user` se usa correctamente.