from fastapi import APIRouter, Request, status, Path
from models.service_offering import ServiceOffering
from controllers import service_offering as controller
from utils.security import validateuser, validateadmin, validateadmin_or_profesional

router = APIRouter(prefix="/service_offerings", tags=["Service Offerings"])

# ============================
# Crear una oferta de servicio (Admin o Profesional)
# ============================
@router.post("/", status_code=status.HTTP_201_CREATED)
@validateadmin_or_profesional
async def create_service_offering_route(service: ServiceOffering, request: Request):
    return await controller.create_service_offering(service)

# ============================
# Obtener todas las ofertas (Todos los usuarios autenticados)
# ============================
@router.get("/", response_model=list[ServiceOffering])
@validateuser
async def get_all_service_offerings_route(request: Request):
    return await controller.get_all_service_offerings()

# ============================
# Obtener oferta por ID (Usuarios autenticados)
# ============================
@router.get("/{id}", response_model=ServiceOffering)
@validateuser
async def get_service_offering_by_id_route(id: str, request: Request):
    return await controller.get_service_offering_by_id(id)

# ============================
# 🔧 Actualizar oferta (Admin o Profesional dueño)
# ============================
@router.put("/{id}", response_model=dict)
@validateadmin_or_profesional
async def update_service_offering_route(
    id: str,
    service: ServiceOffering,
    request: Request
):
    user = request.state.user
    return await controller.update_service_offering(
        service_id=id,
        updated_data=service.model_dump(exclude={"id"}),  # Excluir `id` para evitar conflictos
        user_id=user["id"],
        is_admin=user["admin"]
    )

# ============================
# Eliminar oferta (Solo Admin)
# ============================
@router.delete("/{id}")
@validateadmin
async def delete_service_offering_route(id: str, request: Request):
    return await controller.delete_service_offering(id)

# ============================
# Obtener detalle enriquecido (Usuarios autenticados)
# ============================
@router.get("/{id}/detalle", tags=["Service Offerings - Detalle Enriquecido"]) 
@validateuser
async def get_service_offering_detail_route(id: str, request: Request):
    return await controller.get_full_service_offering(id)




