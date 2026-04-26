import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    # Primero intentamos usar el contenido JSON de la variable de entorno
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        import json
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Si no existe, buscamos la ruta al archivo de credenciales
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            raise RuntimeError(
                "Ninguna credencial de Google configurada. "
                "Define GOOGLE_CREDENTIALS con el JSON completo o "
                "GOOGLE_APPLICATION_CREDENTIALS con la ruta al archivo."
            )
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

    client = gspread.authorize(creds)

    # Obtener el ID de la hoja desde la variable de entorno
    SHEET_ID = os.getenv("SHEET_ID")
    if not SHEET_ID:
        raise RuntimeError("La variable de entorno SHEET_ID no está configurada.")
    
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet