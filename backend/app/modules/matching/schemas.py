from pydantic import BaseModel
from typing import List, Optional

class ProductorRecomendado(BaseModel):
    email: str
    nombre: str
    ubicacion: str
    estrellas: float
    productos_count: int
    productos_destacados: List[str]

class TransportistaRecomendado(BaseModel):
    email: str
    nombre: str
    tipo_vehiculo: str
    zona_cobertura: str
    tarifa_base: int
    costo_km: int

class ProductoRecomendado(BaseModel):
    id: str
    nombre: str
    precio: int
    productor: str
    estrellas: float
    stock: int

class RecomendacionesResponse(BaseModel):
    productores: List[ProductorRecomendado]
    transportistas: List[TransportistaRecomendado]
    productos: List[ProductoRecomendado]