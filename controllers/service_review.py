from fastapi import HTTPException
from models.service_review import ServiceReview
from utils.mongodb import get_collection
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()
coll = get_collection("service_review")

async def create_service_review(service_review: ServiceReview) -> ServiceReview:
    try:
        data = service_review.model_dump(exclude={"id"})
        result = coll.insert_one(data)
        service_review.id = str(result.inserted_id)
        return service_review
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear: {e}")

async def get_all_service_reviews() -> list[ServiceReview]:
    try:
        docs = coll.find()
        return [ServiceReview(id=str(doc["_id"]), **doc) for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reviews: {e}")

async def get_service_review_by_id(review_id: str) -> ServiceReview:
    try:
        doc = coll.find_one({"_id": ObjectId(review_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Review no encontrada")
        return ServiceReview(id=str(doc["_id"]), **doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar review: {e}")

async def delete_service_review(review_id: str):
    try:
        result = coll.delete_one({"_id": ObjectId(review_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No se encontró para eliminar")
        return {"message": "Eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {e}")
