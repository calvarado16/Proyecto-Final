from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone

class Reservation(BaseModel):
    id: Optional[str] = Field(default=None, description="MongoDB ID")

    id_user: str = Field(
        description="ID del usuario que realiza la reservación",
        examples=["507f1f77bcf86cd799439011"]
    )

    reservation_date: datetime = Field(
        description="Fecha y hora para la que se reserva el servicio",
        examples=["2025-08-01T10:30:00Z"]
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha y hora en la que se creó la reservación"
    )

    status: str = Field(
        default="pending",
        description="Estado de la reserva (pending, confirmed, cancelled, completed)",
        examples=["pending"]
    )

    notes: Optional[str] = Field(
        default=None,
        description="Notas adicionales sobre la reserva"
    )

    # Validación del campo 'status'
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = ["pending", "confirmed", "cancelled", "completed"]
        if v not in allowed:
            raise ValueError(f"Estado inválido. Opciones permitidas: {allowed}")
        return v

@field_validator("reservation_date")
@classmethod
def validate_reservation_date(cls, v: datetime):
    now = datetime.now(timezone.utc)
    v = v.astimezone(timezone.utc)
    if v < now:
        raise ValueError("La fecha de la reserva debe ser futura")
    return v





