# controllers/profession.py
from fastapi import HTTPException, Request
from bson import ObjectId
from datetime import datetime

from utils.mongodb import get_collection
from models.profession import Profession

# === Pipelines (los que enviaste) ===
from pipelines.profession_pipelines import (
    get_all_professions_pipeline,
    get_profession_with_service_count_pipeline,
    search_professions_pipeline,
)
from pipelines.profession_type_pipelines import (
    validate_profession_is_assigned_pipeline,
)

coll = get_collection("profession")
services_coll = get_collection("service_offering")  # opcional para conteos directos


# ------------------------------
# Helpers
# ------------------------------
def _to_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

def _serialize(doc: dict) -> dict:
    if not doc:
        return doc
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


# ---------- CREATE ----------
async def create_profession(prof: Profession, request: Request):
    # (Si usas validateuser, aquí ya llega autenticado)
    # Normalizar + validar duplicados
    prof.name = prof.name.strip()
    if getattr(prof, "description", None):
        prof.description = prof.description.strip()

    if coll.find_one({"name": {"$regex": f"^{prof.name}$", "$options": "i"}}):
        raise HTTPException(status_code=400, detail="La profesión ya existe")

    payload = prof.model_dump(exclude={"id"})
    payload.setdefault("active", True)
    payload.setdefault("created_at", datetime.utcnow())
    payload["updated_at"] = datetime.utcnow()

    res = coll.insert_one(payload)
    created = coll.find_one({"_id": res.inserted_id})
    return _serialize(created)


# ---------- READ LIST (via pipeline) ----------
async def get_all_professions(include_inactive: bool, request: Request):

    pipeline = get_all_professions_pipeline(skip=0, limit=10_000, include_inactive=include_inactive)
    return list(coll.aggregate(pipeline))


# ---------- READ ONE ----------
async def get_profession_by_id(id: str, request: Request):
    doc = coll.find_one({"_id": _to_oid(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")
    return _serialize(doc)


# ---------- UPDATE ----------
async def update_profession(id: str, prof: Profession, request: Request):
    oid = _to_oid(id)
    current = coll.find_one({"_id": oid})
    if not current:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    # Normalizar + validar duplicados
    prof.name = prof.name.strip()
    if getattr(prof, "description", None):
        prof.description = prof.description.strip()

    dup = coll.find_one({
        "name": {"$regex": f"^{prof.name}$", "$options": "i"},
        "_id": {"$ne": oid}
    })
    if dup:
        raise HTTPException(status_code=400, detail="Ya existe otra profesión con ese nombre")

    payload = prof.model_dump(exclude={"id"})
    payload["updated_at"] = datetime.utcnow()

    coll.update_one({"_id": oid}, {"$set": payload})
    updated = coll.find_one({"_id": oid})
    return _serialize(updated)


# ---------- DELETE (SIEMPRE SOFT-DELETE) ----------
async def delete_profession_safe(id: str, request: Request):

    oid = _to_oid(id)
    existing = coll.find_one({"_id": oid})
    if not existing:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    # Conteo de servicios asociados vía pipeline (el que enviaste)
    validation = list(coll.aggregate(validate_profession_is_assigned_pipeline(id)))
    linked = 0
    if validation:
        linked = int(validation[0].get("number_of_services", 0))

    # Soft delete: active=False
    coll.update_one(
        {"_id": oid},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )

    return {
        "status": "deactivated",
        "message": "La profesión se desactivó correctamente (no se elimina físicamente).",
        "id": id,
        "linked_services": linked,
    }


# ---------- PIPELINE ENDPOINTS AUX ----------
async def professions_with_service_count(request: Request):
 
    return list(coll.aggregate(get_profession_with_service_count_pipeline()))

async def search_professions(q: str, skip: int, limit: int, request: Request):

    return list(coll.aggregate(search_professions_pipeline(q, skip, limit)))

async def validate_profession_is_assigned(id: str, request: Request):

    result = list(coll.aggregate(validate_profession_is_assigned_pipeline(id)))
    if not result:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")
    # El pipeline ya proyecta con id/name/active/number_of_services
    return result[0]


# ---- Alias para compatibilidad (si algún router antiguo lo importa) ----
async def get_professions(include_inactive: bool, request: Request):
    return await get_all_professions(include_inactive, request)
