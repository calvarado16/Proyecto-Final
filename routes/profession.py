from fastapi import APIRouter, HTTPException, Request
from models.profession import Profession
from controllers.profession import (
    create_profession,
    get_all_professions,
    get_profession_by_id,
    update_profession,
    delete_profession
)
from utils.security import validateadmin

router = APIRouter(prefix="/profession", tags=["Profession"])

# ============================
# Crear profesión
# ============================
@router.post("/", response_model=Profession)
@validateadmin
async def create_profession_endpoint(request: Request, profession: Profession) -> Profession:
    return await create_profession(profession)

# ============================
# Obtener todas las profesiones
# ============================
@router.get("/", response_model=list[Profession])
async def get_all_professions_endpoint() -> list[Profession]:
    return await get_all_professions()

# ============================
# Obtener una profesión por ID
# ============================
@router.get("/{profession_id}", response_model=Profession)
async def get_profession_by_id_endpoint(profession_id: str) -> Profession:
    return await get_profession_by_id(profession_id)

# ============================
# Actualizar una profesión
# ============================
@router.put("/{profession_id}", response_model=dict)
@validateadmin
async def update_profession_endpoint(request: Request, profession_id: str, profession: Profession) -> dict:
    return await update_profession(profession_id, profession)

# ============================
# Eliminar una profesión
# ============================
@router.delete("/{profession_id}", response_model=dict)
@validateadmin
async def delete_profession_endpoint(request: Request, profession_id: str) -> dict:
    return await delete_profession(profession_id)


