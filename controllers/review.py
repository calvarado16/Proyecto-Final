import os
from dotenv import load_dotenv
from fastapi import HTTPException
from models.review import Review
from utils.mongodb import get_collection
from bson import ObjectId
from datetime import datetime

load_dotenv()

URI = os.getenv("URI")
coll = get_collection("reviews")
services_coll = get_collection("service_offering")

# Crear una reseña
async def create_review(review: Review) -> Review:
    try:
        # Validar que el servicio al que se refiere la reseña existe
        service_id = review.id_service_offering
        if not ObjectId.is_valid(service_id):
            raise HTTPException(status_code=400, detail="ID de servicio inválido")

        service = services_coll.find_one({"_id": ObjectId(service_id)})
        if not service:
            raise HTTPException(status_code=404, detail="El servicio no existe")

        review_dict = review.model_dump(exclude={"id"})
        review_dict["created_at"] = datetime.utcnow()

        result = coll.insert_one(review_dict)
        review.id = str(result.inserted_id)
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear reseña: {str(e)}")

# Obtener todas las reseñas
async def get_all_reviews() -> list[Review]:
    try:
        docs = coll.find()
        reviews = []
        for doc in docs:
            doc["id"] = str(doc["_id"])
            reviews.append(Review(**doc))
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reseñas: {str(e)}")

# Obtener una reseña por ID
async def get_review_by_id(id: str) -> Review:
    try:
        doc = coll.find_one({"_id": ObjectId(id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        doc["id"] = str(doc["_id"])
        return Review(**doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar reseña: {str(e)}")

# Actualizar reseña
async def update_review(id: str, review: Review) -> Review:
    try:
        existing = coll.find_one({"_id": ObjectId(id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")

        update_data = review.model_dump(exclude={"id"})
        coll.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        review.id = id
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar reseña: {str(e)}")

# Eliminar reseña
async def delete_review(id: str):
    try:
        result = coll.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Reseña no encontrada")
        return {"message": "Reseña eliminada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar reseña: {str(e)}")


