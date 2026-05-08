from datetime import datetime, timezone, timedelta

# Diferencia horaria de Colombia: UTC-5
COLOMBIA_TZ = timezone(timedelta(hours=-5))

def utc_to_colombia(dt: datetime) -> datetime:
    """Convierte un datetime (asumido UTC) a la zona horaria de Colombia."""
    if dt is None:
        return None
    # Si el datetime es timezone-aware, lo convertimos; si no, asumimos UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(COLOMBIA_TZ)