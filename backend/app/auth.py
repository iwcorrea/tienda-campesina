import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .models import Asociacion

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-cambiar")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session) -> Asociacion:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(Asociacion).filter(Asociacion.email == email).first()
    if user is None:
        raise credentials_exception

    return user
