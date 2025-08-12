import os
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from pymongo import ReturnDocument

from models.reservation import Reservation
from utils.mongodb import get_collection

URI = os.getenv("URI")
collection = get_collection("reservations")
users_collection = get_collection("users")

async def create_reservation(reservation: Reservation) -> Reservation:
    try:
        user_id = ObjectId(reservation.id_user)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    user_exists = users_collection.find_one({"_id": user_id})
    if not user_exists:
        raise HTTPException(status_code=404, detail="El usuario referenciado no existe")

    reservation_dict = reservation.model_dump(exclude={"id"})
    result = collection.insert_one(reservation_dict)
    reservation.id = str(result.inserted_id)
    return reservation

async def get_all_reservations() -> list[Reservation]:
    docs = collection.find()
    return [Reservation(**{**doc, "id": str(doc["_id"])}) for doc in docs]

async def get_reservation_by_id(id: str) -> Reservation:
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    doc = collection.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    return Reservation(**{**doc, "id": str(doc["_id"])})

async def update_reservation(id: str, reservation: Reservation) -> Reservation:
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    existing = collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")

    hours_before = int(os.getenv("HOURS_BEFORE_UPDATE", 2))
    time_diff = (existing["reservation_date"] - datetime.utcnow()).total_seconds() / 3600
    if time_diff < hours_before:
        raise HTTPException(status_code=400, detail=f"Solo se puede modificar con al menos {hours_before} horas de anticipación")

    updated_doc = collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": reservation.model_dump(exclude={"id", "created_at"}, exclude_unset=True)},
        return_document=ReturnDocument.AFTER
    )
    return Reservation(**{**updated_doc, "id": str(updated_doc["_id"])})

async def delete_reservation(id: str):
    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID inválido")

    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    return {"message": "Reservación eliminada correctamente"}


