from fastapi import APIRouter, Request, status
from models.reservation import Reservation
from controllers import reservation as reservation_controller
from utils.security import validateuser, validateadmin

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_reservation_route(reservation: Reservation, request: Request):
    return await reservation_controller.create_reservation(reservation)

@router.get("/", response_model=list[Reservation])
@validateadmin
async def get_all_reservations_route(request: Request):
    return await reservation_controller.get_all_reservations()

@router.get("/{id}", response_model=Reservation)
@validateuser
async def get_reservation_by_id_route(id: str, request: Request):
    return await reservation_controller.get_reservation_by_id(id)

@router.put("/{id}", response_model=Reservation)
@validateuser
async def update_reservation_route(id: str, reservation: Reservation, request: Request):
    return await reservation_controller.update_reservation(id, reservation)

@router.delete("/{id}")
@validateadmin
async def delete_reservation_route(id: str, request: Request):
    return await reservation_controller.delete_reservation(id)

