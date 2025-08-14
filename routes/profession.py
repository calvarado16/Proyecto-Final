# routes/profession.py
from fastapi import APIRouter, Request, status, Query, Path
from models.profession import Profession
from controllers import profession as controller
from utils.security import validateuser

router = APIRouter(prefix="/profession", tags=["Profession"])

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_profession_route(body: Profession, request: Request):
    return await controller.create_profession(body, request)

# 👇 PASA request al controlador y quita response_model (evita errores de validación si el pipeline añade campos)
@router.get("/")
@validateuser
async def get_all_professions_route(
    request: Request,
    include_inactive: bool = Query(False, description="Incluir inactivas")
):
    return await controller.get_all_professions(include_inactive, request)

@router.get("/{id}")
@validateuser
async def get_profession_by_id_route(
    id: str = Path(..., description="ID de la profesión"),
    request: Request = None
):
    return await controller.get_profession_by_id(id, request)

@router.put("/{id}")
@validateuser
async def update_profession_route(id: str, body: Profession, request: Request):
    return await controller.update_profession(id, body, request)

@router.delete("/{id}")
@validateuser
async def delete_profession_route(id: str, request: Request):
    return await controller.delete_profession_safe(id, request)

# ---------------------------
# ENDPOINTS que usan pipelines extra
# ---------------------------
@router.get("/with-service-count")
@validateuser
async def professions_with_service_count_route(request: Request):
    return await controller.professions_with_service_count(request)

@router.get("/search")
@validateuser
async def search_professions_route(
    q: str = Query(..., description="Texto a buscar en nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    request: Request = None
):
    return await controller.search_professions(q, skip, limit, request)

@router.get("/{id}/validate-assigned")
@validateuser
async def validate_profession_assigned_route(id: str, request: Request):
    return await controller.validate_profession_is_assigned(id, request)




