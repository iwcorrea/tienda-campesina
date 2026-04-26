import json
import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    """
    Autentica con Google Sheets usando la cuenta de servicio.
    Primero busca la variable de entorno GOOGLE_CREDENTIALS (producción).
    Si no existe, busca el archivo JSON local (desarrollo).
    """
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        # Render: el JSON completo viene en la variable de entorno
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Local: leer archivo .json (ajusta el nombre exacto de tu archivo)
        creds = Credentials.from_service_account_file(
            "credenciales.json", scopes=SCOPES
        )

    client = gspread.authorize(creds)
    # 🔁 REEMPLAZA ESTE ID con el de tu hoja de cálculo
    SPREADSHEET_ID = "1A2B3C4D5E6F7G8H9I0J"   # ← ¡Cámbialo!
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet