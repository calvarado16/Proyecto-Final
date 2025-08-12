from pydantic import BaseModel, Field
from typing import Optional
import re


class ServiceOffering(BaseModel):
    id: str = Field(
        id="_id", 
        default=None, 
        description="MongoDB ID"
        )
    
    id_profesional: str = Field( 
        description="ID del profesional que ofrece el servicio"
        )
    
    description: str = Field( 
        description="Descripción del servicio"
        )
    
    price_per_hour: float = Field( 
        gt=0, 
        description="Precio por hora del servicio"
        )
    estimate_work_time: str = Field(
        description="Tiempo estimado de trabajo (ej: '2 horas')"
        )
    work_type: str = Field(
        description="Tipo de trabajo "
        )
    active: bool = Field(
        default=True, 
        description="Indica si el servicio está activo o no"
        )

    class Config:
        schema_extra = {
            "example": {
                "id_profesional": "60f6e6e1f2954b0c2e4e9e88",
                "description": "Reparación de computadoras a domicilio",
                "price_per_hour": 25.5,
                "estimate_work_time": "2 horas",
                "work_type": "presencial",
                "active": True
            }
        }
