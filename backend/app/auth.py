from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import models, database
import os
from datetime import datetime, timedelta, timezone

# ... (resto de tu código para hash, etc.) ...

# Cambia el nombre de la función aquí:
def obtener_usuario_actual(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        usuario = db.query(models.Asociacion).filter(models.Asociacion.id == int(user_id)).first()
        if usuario is None:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return usuario
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")