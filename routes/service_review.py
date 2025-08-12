from fastapi import APIRouter, status, Request
from models.service_review import ServiceReview
from controllers import service_review as controller
from utils.security import validateuser

router = APIRouter(prefix="/service_reviews", tags=["ServiceReview"])

@router.post("/", status_code=status.HTTP_201_CREATED)
@validateuser
async def create(service_review: ServiceReview, request: Request):
    return await controller.create_service_review(service_review)

@router.get("/", response_model=list[ServiceReview])
@validateuser
async def get_all(request: Request):
    return await controller.get_all_service_reviews()

@router.get("/{review_id}", response_model=ServiceReview)
@validateuser
async def get_by_id(review_id: str, request: Request):
    return await controller.get_service_review_by_id(review_id)

@router.delete("/{review_id}")
@validateuser
async def delete_by_id(review_id: str, request: Request):
    return await controller.delete_service_review(review_id)
