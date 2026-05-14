from pydantic import BaseModel, EmailStr, validator
import re

class RegistroAsociacionRequest(BaseModel):
    email: str
    password: str
    nombre: str
    descripcion: str = ""
    direccion: str = ""
    telefono: str = ""

    @validator('password')
    def validar_contraseña(cls, v):
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Debe incluir al menos una letra mayúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Debe incluir al menos una letra minúscula.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Debe incluir al menos un número.')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', v):
            raise ValueError('Debe incluir al menos un símbolo especial.')
        return v

class RegistroPersonaRequest(BaseModel):
    email: str
    password: str
    nombre: str
    telefono: str = ""

    @validator('password')
    def validar_contraseña(cls, v):
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Debe incluir al menos una letra mayúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Debe incluir al menos una letra minúscula.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Debe incluir al menos un número.')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', v):
            raise ValueError('Debe incluir al menos un símbolo especial.')
        return v

class RegistroTransportistaRequest(BaseModel):
    email: str
    password: str
    nombre: str
    telefono: str = ""
    tipo_vehiculo: str = "camioneta"
    capacidad: str = "500 kg"
    zona_cobertura: str = "Local"
    tarifa_base: int = 5000
    costo_km: int = 1500

    @validator('password')
    def validar_contraseña(cls, v):
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Debe incluir al menos una letra mayúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Debe incluir al menos una letra minúscula.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Debe incluir al menos un número.')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', v):
            raise ValueError('Debe incluir al menos un símbolo especial.')
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

class CambioPasswordRequest(BaseModel):
    password_actual: str
    password_nueva: str
    password_confirmacion: str

    @validator('password_nueva')
    def validar_contraseña(cls, v):
        if len(v) < 12:
            raise ValueError('La contraseña debe tener al menos 12 caracteres.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Debe incluir al menos una letra mayúscula.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Debe incluir al menos una letra minúscula.')
        if not re.search(r'[0-9]', v):
            raise ValueError('Debe incluir al menos un número.')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', v):
            raise ValueError('Debe incluir al menos un símbolo especial.')
        return v