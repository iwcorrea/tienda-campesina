from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Forzar el uso de un diccionario vacío para la caché (evita el error de clave no hasheable)
templates.env.cache = {}