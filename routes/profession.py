from fastapi import APIRouter, Request, status, Path
from models.profession import Profession
from controllers import profession as controller
from utils.security import validateuser

router = APIRouter(prefix="/profession", tags=["Profession"])

@router.get("/", response_model=list[Profession])
@validateuser
async def list_professions(request: Request):
    return await controller.list_professions_active()

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_profession(prof: Profession, request: Request):
    return await controller.create_profession(prof, actor_id=request.state.id)

@router.put("/{id}")
@validateuser
async def update_profession(id: str, prof: Profession, request: Request):
    return await controller.update_profession(
        id,
        prof,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False))
    )

@router.delete("/{id}")
@validateuser
async def delete_profession(id: str, request: Request):
    return await controller.delete_profession(
        id,
        actor_id=request.state.id,
        is_admin=bool(getattr(request.state, "admin", False))
    )


