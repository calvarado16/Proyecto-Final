import os
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, Request
from pymongo import ReturnDocument
from datetime import datetime

from models.service_offering import ServiceOffering
from utils.mongodb import get_collection
from pipelines.service_offering_pipeline import get_full_service_offering_pipeline

URI = os.getenv("URI")
DB = os.getenv("MONGO_DB_NAME")

collection = get_collection("service_offerings")
users_collection = get_collection("users")

# ============================
# Crear oferta
# ============================
async def create_service_offering(service: ServiceOffering) -> ServiceOffering:
    try:
        profesional_id = ObjectId(service.id_profesional)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID de profesional inválido")

    user_exists = users_collection.find_one({"_id": profesional_id})
    if not user_exists:
        raise HTTPException(status_code=404, detail="El profesional no existe")

    service_dict = service.model_dump(exclude={"id"})
    service_dict["created_at"] = datetime.utcnow()

    result = collection.insert_one(service_dict)
    service.id = str(result.inserted_id)
    return service

# ============================
# Obtener todas
# ============================
async def get_all_service_offerings() -> list[ServiceOffering]:
    docs = collection.find()
    return [ServiceOffering(**{**doc, "id": str(doc["_id"])}) for doc in docs]

# ============================
# Obtener por ID
# ============================
async def get_service_offering_by_id(id: str) -> ServiceOffering:
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    doc = collection.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    return ServiceOffering(**{**doc, "id": str(doc["_id"])})

# ============================
# Actualizar (Admin o dueño profesional)
# ============================
async def update_service_offering(id: str, service: ServiceOffering, request: Request) -> ServiceOffering:
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    existing = collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    user_id = request.state.id
    is_admin = getattr(request.state, "admin", False)

    if not is_admin and str(existing.get("id_profesional")) != str(user_id):
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este servicio")

    updated_doc = collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": service.model_dump(exclude={"id", "created_at"}, exclude_unset=True)},
        return_document=ReturnDocument.AFTER
    )

    return ServiceOffering(**{**updated_doc, "id": str(updated_doc["_id"])})

# ============================
# Eliminar (Admin o dueño profesional)
# ============================
async def delete_service_offering(id: str, request: Request):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    existing = collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    user_id = request.state.id
    is_admin = getattr(request.state, "admin", False)

    if not is_admin and str(existing.get("id_profesional")) != str(user_id):
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este servicio")

    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Error al eliminar el servicio")

    return {"message": "Servicio eliminado correctamente"}

# ============================
# 🔍 Detalle enriquecido con pipeline
# ============================
async def get_full_service_offering(service_id: str) -> dict:
    try:
        if not ObjectId.is_valid(service_id):
            raise HTTPException(status_code=400, detail="ID inválido")

        pipeline = get_full_service_offering_pipeline(service_id)
        result = list(collection.aggregate(pipeline))

        if not result:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")

        return {"success": True, "data": result[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pipeline: {e}")



