from fastapi import APIRouter, Request, status
from models.review import Review
from controllers import review as controller
from utils.security import validateuser, validateadmin

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# ============================
# Crear una reseña
# ============================
@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create_review_route(review: Review, request: Request):
    return await controller.create_review(review)

# ============================
# Obtener todas las reseñas (Solo admin)
# ============================
@router.get("/", response_model=list[Review])
@validateadmin
async def get_all_reviews_route(request: Request):
    return await controller.get_all_reviews()

# ============================
# Obtener una reseña por ID
# ============================
@router.get("/{id}", response_model=Review)
@validateuser
async def get_review_by_id_route(id: str, request: Request):
    return await controller.get_review_by_id(id)

# ============================
# Actualizar una reseña
# ============================
@router.put("/{id}", response_model=Review)
@validateuser
async def update_review_route(id: str, review: Review, request: Request):
    return await controller.update_review(id, review)

# ============================
# Eliminar una reseña (Solo admin)
# ============================
@router.delete("/{id}")
@validateadmin
async def delete_review_route(id: str, request: Request):
    return await controller.delete_review(id)

# ============================
# Estadísticas de reviews (Pipeline $group)
# ============================
@router.get("/estadisticas", tags=["Reviews - Estadísticas"])
@validateadmin
async def get_review_stats_route(request: Request):
    return await controller.get_review_stats_by_service()


