from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson import ObjectId

class Review(BaseModel):
    id: Optional[str] = Field(default=None, description="MongoDB ID")
    id_usuario: str = Field(..., description="ID del usuario que deja la reseña")
    id_service_offering: str = Field(..., description="ID del servicio evaluado")
    opinion: str = Field(..., description="Opinión del usuario")
    rating: float = Field(..., ge=0, le=5, description="Calificación entre 0 y 5")

    @field_validator("id_usuario", "id_service_offering")
    @classmethod
    def validate_object_id(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Debe ser un ObjectId válido")
        return value


