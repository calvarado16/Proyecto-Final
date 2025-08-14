from typing import Optional
from pydantic import BaseModel, Field

class ServiceOffering(BaseModel):
    
    id: Optional[str] = Field(
        default=None,
        alias="_id",
        description="MongoDB ObjectId (hex) como string"
    )

    id_profession: str = Field(
        ...,
        description="ObjectId (hex) de la profesión relacionada"
    )

    description: str = Field(
        ...,
        min_length=3,
        description="Descripción del servicio"
    )

    estimated_price: int = Field(
        ...,
        ge=0,
        description="Precio estimado del servicio (entero)"
    )

    estimated_duration: int = Field(
        ...,
        ge=1,
        description="Duración estimada en minutos"
    )

    active: bool = Field(
        default=True,
        description="Indica si el servicio está activo"
    )

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "id_profession": "60f6e6e1f2954b0c2e4e9e88",
                "description": "Reparación de computadoras a domicilio",
                "estimated_price": 500,
                "estimated_duration": 90,
                "active": True
            }
        }
