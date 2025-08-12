from pydantic import BaseModel, Field
from typing import Optional

class ServiceReview(BaseModel):
    id: Optional[str] = Field(default=None, description="MongoDB ID del review")
    id_service: str = Field(..., description="ID del servicio")
    id_reservation: str = Field(..., description="ID de la reservación")
    id_review: str = Field(..., description="ID de la reseña")
    calification: str = Field(..., description="Calificación del servicio (texto)")
