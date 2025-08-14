# routes/service_offering.py
from fastapi import APIRouter, Request, status, Path
from models.service_offering import ServiceOffering
from controllers import service_offering as controller
from utils.security import validateuser

router = APIRouter(prefix="/service_offering", tags=["Service Offering"])

@router.get("/", summary="Listar servicios activos (con profession_name)")
@validateuser
async def get_services(request: Request):
    # Devuelve la lista enriquecida por pipeline (incluye profession_name)
    return await controller.list_services_active()

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Crear servicio")
@validateuser
async def create_service(service: ServiceOffering, request: Request):
    # Crea y devuelve el servicio ya pasado por pipeline
    return await controller.create_service(service, actor_id=request.state.id)

@router.put("/{id}", summary="Actualizar servicio")
@validateuser
async def update_service(
    id: str = Path(..., description="ID del servicio"),
    service: ServiceOffering = None,
    request: Request = None,
):
    # Actualiza y devuelve el servicio ya pasado por pipeline
    return await controller.update_service(
        id,
        service,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False)),
    )

@router.delete("/{id}", summary="Desactivar servicio (soft delete)")
@validateuser
async def delete_service(id: str, request: Request):
    # Soft delete: active=False (mantiene integridad)
    return await controller.delete_service(
        id,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False)),
    )




