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

@router.get("/", response_model=list[Profession])
@validateuser
async def get_all_professions_route(
    request: Request,
    include_inactive: bool = Query(False, description="Incluir inactivas")
):
    return await controller.get_all_professions(include_inactive)

@router.get("/{id}", response_model=Profession)
@validateuser
async def get_profession_by_id_route(id: str, request: Request):
    return await controller.get_profession_by_id(id)

@router.put("/{id}")
@validateuser
async def update_profession_route(id: str, body: Profession, request: Request):
    return await controller.update_profession(id, body, request)

@router.delete("/{id}")
@validateuser
async def delete_profession_route(id: str, request: Request):
    return await controller.delete_profession_safe(id, request)



