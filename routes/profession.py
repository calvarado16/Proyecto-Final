# routes/profession.py
from fastapi import APIRouter, HTTPException, Request, status, Query, Path
from models.profession import Profession
from controllers.profession import (
    create_profession,
    get_all_professions,            # <-- corregido
    get_profession_by_id,
    update_profession,
    delete_profession_safe,
    professions_with_service_count,
    search_professions,
    validate_profession_is_assigned,
)
from utils.security import validateuser

router = APIRouter(prefix="/professions", tags=["📂 Professions"])

@router.post("/", response_model=Profession, status_code=status.HTTP_201_CREATED)
@validateuser
async def create_profession_endpoint(request: Request, body: Profession) -> Profession:
    """Crear una profesión"""
    return await create_profession(body, request)

@router.get("/", response_model=list[Profession])
async def get_professions_endpoint(
    request: Request,                                        # <-- agrega request
    include_inactive: bool = Query(False, description="Incluir inactivas")
) -> list[Profession]:
    """Listar profesiones"""
    return await get_all_professions(include_inactive, request)  # <-- pasa request

@router.get("/{id}", response_model=Profession)
async def get_profession_by_id_endpoint(
    id: str = Path(..., description="ID de la profesión"),
    request: Request = None                                   # <-- agrega request
) -> Profession:
    """Obtener profesión por ID"""
    return await get_profession_by_id(id, request)            # <-- pasa request

@router.put("/{id}", response_model=Profession)
@validateuser
async def update_profession_endpoint(
    request: Request,
    id: str,
    body: Profession
) -> Profession:
    """Actualizar una profesión"""
    return await update_profession(id, body, request)

@router.delete("/{id}", response_model=dict, tags=["📂 Professions"])
@validateuser
async def delete_profession_safe_endpoint(
    request: Request,
    id: str
) -> dict:
    """
    Borrado seguro de una profesión:
    - Si tiene servicios asociados -> desactiva (active=False)
    - Si no tiene -> elimina definitivamente
    """
    return await delete_profession_safe(id, request)          # <-- indentación correcta

# Extras opcionales
@router.get("/with-service-count", response_model=list[dict])
@validateuser
async def professions_with_service_count_endpoint(
    request: Request                                         # <-- agrega request
) -> list[dict]:
    return await professions_with_service_count(request)      # <-- pasa request

@router.get("/search", response_model=list[Profession])
@validateuser
async def search_professions_endpoint(
    request: Request,                                         # <-- agrega request
    q: str = Query(..., description="Texto a buscar en nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
) -> list[Profession]:
    return await search_professions(q, skip, limit, request)  # <-- pasa request

@router.get("/{id}/validate-assigned", response_model=dict)
@validateuser
async def validate_profession_assigned_endpoint(
    request: Request,                                         # <-- agrega request
    id: str
) -> dict:
    return await validate_profession_is_assigned(id, request) # <-- pasa request







