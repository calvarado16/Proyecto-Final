from fastapi import APIRouter, Request, status
from models.reservation_service import ReservationService
from controllers import reservation_service as controller
from utils.security import validateuser, validateadmin

router = APIRouter(prefix="/reservation_services", tags=["Reservation Services"])

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_route(data: ReservationService, request: Request):
    return await controller.create_reservation_service(data)

@router.get("/", response_model=list[ReservationService])
@validateadmin
async def get_all_route(request: Request):
    return await controller.get_all_reservation_services()

@router.get("/{id}", response_model=ReservationService)
@validateuser
async def get_by_id_route(id: str, request: Request):
    return await controller.get_reservation_service_by_id(id)

@router.put("/{id}", response_model=ReservationService)
@validateuser
async def update_route(id: str, data: ReservationService, request: Request):
    return await controller.update_reservation_service(id, data)

@router.delete("/{id}")
@validateadmin
async def delete_route(id: str, request: Request):
    return await controller.delete_reservation_service(id)
