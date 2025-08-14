from fastapi import APIRouter, Request, status, Path
from models.service_offering import ServiceOffering
from controllers import service_offering as controller
from utils.security import validateuser

router = APIRouter(prefix="/service_offering", tags=["Service Offering"])

@router.get("/", response_model=list[ServiceOffering])
@validateuser
async def get_services(request: Request):
    return await controller.list_services_active()

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_service(service: ServiceOffering, request: Request):
    return await controller.create_service(service, actor_id=request.state.id)

@router.put("/{id}")
@validateuser
async def update_service(
    id: str = Path(..., description="ID del servicio"),
    service: ServiceOffering = None,
    request: Request = None
):
    return await controller.update_service(
        id,
        service,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False))
    )

@router.delete("/{id}")
@validateuser
async def delete_service(id: str, request: Request):
    return await controller.delete_service(
        id,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False))
    )




