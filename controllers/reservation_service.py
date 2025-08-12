from fastapi import HTTPException
from models.reservation_service import ReservationService
from utils.mongodb import get_collection
from bson import ObjectId
from datetime import datetime
import os

coll = get_collection("reservation_service")

async def create_reservation_service(data: ReservationService) -> ReservationService:
    try:
        new_data = data.model_dump(exclude={"id"})
        result = coll.insert_one(new_data)
        data.id = str(result.inserted_id)
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Error al crear ReservationService")

async def get_all_reservation_services() -> list[ReservationService]:
    try:
        return [ReservationService(**{**doc, "id": str(doc["_id"])}) for doc in coll.find()]
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener datos")

async def get_reservation_service_by_id(id: str) -> ReservationService:
    try:
        doc = coll.find_one({"_id": ObjectId(id)})
        if not doc:
            raise HTTPException(status_code=404, detail="No encontrado")
        doc["id"] = str(doc["_id"])
        return ReservationService(**doc)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al buscar dato")

async def update_reservation_service(id: str, data: ReservationService) -> ReservationService:
    try:
        updated = coll.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": data.model_dump(exclude={"id", "created_at"})},
            return_document=True
        )
        if not updated:
            raise HTTPException(status_code=404, detail="No encontrado")
        updated["id"] = str(updated["_id"])
        return ReservationService(**updated)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al actualizar")

async def delete_reservation_service(id: str):
    try:
        result = coll.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No encontrado")
        return {"message": "Eliminado correctamente"}
    except Exception:
        raise HTTPException(status_code=500, detail="Error al eliminar")
