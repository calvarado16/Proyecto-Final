from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReservationService(BaseModel):
    id: Optional[str] = Field(default=None, description="MongoDB ObjectId")
    id_reservation: str = Field(..., description="ID de la reservación")
    id_service_offering: str = Field(..., description="ID del servicio ofrecido")
    quantity: int = Field(..., gt=0, description="Cantidad del servicio reservado")
    notes: Optional[str] = Field(default=None, description="Notas adicionales")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
