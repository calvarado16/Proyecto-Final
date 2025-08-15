# routes/profession.py
from fastapi import APIRouter, Request, Query
from models.profession import Profession
from controllers import profession as controller
from utils.security import validateuser

router = APIRouter(prefix="/profession", tags=["📌 Profession"])


# ============================
# Crear una profesión
# ============================
@router.post("/", response_model=Profession)
@validateuser
async def create_profession_endpoint(request: Request, profession: Profession) -> Profession:
    """Crear una nueva profesión"""
    return await controller.create_profession(profession, request)


# ============================
# Obtener todas las profesiones
# ============================
@router.get("/", response_model=list[dict])
@validateuser
async def get_professions_endpoint(
    request: Request,
    include_inactive: bool = Query(False, description="Incluir profesiones inactivas")
) -> list[dict]:
    """Obtener todas las profesiones (usa pipeline)"""
    return await controller.get_all_professions(include_inactive, request)


# ============================
# Obtener una profesión por ID
# ============================
@router.get("/{profession_id}", response_model=Profession)
@validateuser
async def get_profession_by_id_endpoint(profession_id: str, request: Request) -> Profession:
    """Obtener una profesión por ID"""
    return await controller.get_profession_by_id(profession_id, request)


# ============================
# Actualizar una profesión
# ============================
@router.put("/{profession_id}", response_model=Profession)
@validateuser
async def update_profession_endpoint(
    request: Request,
    profession_id: str,
    profession: Profession
) -> Profession:
    """Actualizar una profesión"""
    return await controller.update_profession(profession_id, profession, request)


# ============================
# Desactivar una profesión (soft-delete)
# ============================
@router.delete("/{profession_id}", response_model=dict)
@validateuser
async def deactivate_profession_endpoint(request: Request, profession_id: str) -> dict:

    return await controller.delete_profession_safe(profession_id, request)


# ============================
# Endpoint extra: profesiones con número de servicios
# ============================
@router.get("/with-service-count", response_model=list[dict])
@validateuser
async def professions_with_service_count_endpoint(request: Request) -> list[dict]:
    """Lista las profesiones con el número de servicios asociados"""
    return await controller.professions_with_service_count(request)


# ============================
# Endpoint extra: búsqueda
# ============================
@router.get("/search/{term}", response_model=list[dict])
@validateuser
async def search_professions_endpoint(
    term: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    request: Request = None
) -> list[dict]:
    """Buscar profesiones por nombre"""
    return await controller.search_professions(term, skip, limit, request)


# ============================
# Endpoint extra: validar si está asignada
# ============================
@router.get("/validate-assigned/{profession_id}", response_model=dict)
@validateuser
async def validate_profession_assigned_endpoint(profession_id: str, request: Request) -> dict:
    """Valida si la profesión tiene servicios asociados"""
    return await controller.validate_profession_is_assigned(profession_id, request)
