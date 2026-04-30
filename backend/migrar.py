import os
import sys
sys.path.insert(0, ".")
from app.database import SessionLocal, engine
from app.models import Base, Asociacion, Producto, Valoracion
from app.google_sheets import get_sheet, get_products_sheet, get_valoraciones_sheet
import uuid
from datetime import datetime

# Crear tablas en Supabase si no existen
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# --- Migrar asociaciones (Sheet1) ---
sheet_usr = get_sheet()
usuarios = sheet_usr.get_all_values()[1:]  # salta encabezados
for u in usuarios:
    if not u[0]:
        continue
    # Asegurar 12 columnas mínimas (email, hash, fecha, nombre, desc, dir, tel, logo, whatsapp, camara, rut, verificado)
    while len(u) < 12:
        u.append("")
    a = Asociacion(
        id=str(uuid.uuid4()),
        email=u[0],
        hashed_password=u[1],  # ya está encriptado
        nombre=u[3] or u[0],
        descripcion=u[4] or "",
        direccion=u[5] or "",
        telefono=u[6] or "",
        logo_url=u[7] or "",
        show_whatsapp=u[8] or "",
        camara_url=u[9] or "",
        rut_url=u[10] or "",
        verificado=u[11] or ""
    )
    db.add(a)

# --- Migrar productos ---
sheet_prod = get_products_sheet()
productos = sheet_prod.get_all_values()[1:]
for p in productos:
    if len(p) < 9:
        continue
    prod = Producto(
        id=p[0] if p[0] else str(uuid.uuid4()),
        asociacion_email=p[1],
        nombre=p[2] or "",
        descripcion=p[3] or "",
        precio=int(p[4]) if p[4] and p[4].isdigit() else 0,
        imagen_url=p[5] or "",
        tipo=p[7] or "producto",
        tipo_precio=p[8] or "fijo"
    )
    db.add(prod)

# --- Migrar valoraciones ---
try:
    sheet_val = get_valoraciones_sheet()
    vals = sheet_val.get_all_values()[1:]
    for v in vals:
        if len(v) < 6:
            continue
        val = Valoracion(
            id=v[0] if v[0] else str(uuid.uuid4()),
            producto_id=v[1],
            estrellas=int(v[2]) if v[2] and v[2].isdigit() else 0,
            comentario=v[3] or "",
            email_usuario=v[5] or ""
        )
        db.add(val)
except Exception:
    pass

db.commit()
db.close()
print("Migración completada con éxito.")