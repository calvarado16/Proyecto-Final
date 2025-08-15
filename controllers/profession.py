# controllers/profession.py
from fastapi import HTTPException, Request
from bson import ObjectId
from datetime import datetime

from utils.mongodb import get_collection
from models.profession import Profession

# Pipelines existentes
from pipelines.profession_pipelines import (
    get_all_professions_pipeline,
    get_profession_with_service_count_pipeline,
    search_professions_pipeline,
)
from pipelines.profession_type_pipelines import (
    validate_profession_is_assigned_pipeline,
)

col_professions = get_collection("profession")
col_services = get_collection("service_offering")  # <- usado para dependencias


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
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    # Duplicado por nombre
    if col_professions.find_one({"name": prof.name}):
        raise HTTPException(status_code=400, detail="La profesión ya existe")

    payload = prof.model_dump(exclude={"id"})
    payload.setdefault("active", True)
    payload["created_by"] = user.get("id")
    payload["created_at"] = datetime.utcnow()
    payload["updated_at"] = datetime.utcnow()

    res = col_professions.insert_one(payload)
    created = col_professions.find_one({"_id": res.inserted_id})
    return _serialize(created)


# ---------- READ LIST (via pipeline) ----------
async def get_all_professions(include_inactive: bool, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")

    pipeline = get_all_professions_pipeline(
        skip=0, limit=10_000, include_inactive=include_inactive
    )
    return list(col_professions.aggregate(pipeline))


# ---------- READ ONE ----------
async def get_profession_by_id(id: str, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")

    doc = col_professions.find_one({"_id": _to_oid(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")
    return _serialize(doc)


# ---------- UPDATE ----------
async def update_profession(id: str, prof: Profession, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    oid = _to_oid(id)
    current = col_professions.find_one({"_id": oid})
    if not current:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    is_admin = bool(user.get("admin"))
    is_owner = str(current.get("created_by")) == str(user.get("id"))
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=403,
            detail="Solo el creador o un administrador puede actualizar esta profesión",
        )

    payload = prof.model_dump(exclude_unset=True, exclude={"id", "created_by"})
    if "name" in payload:
        dup = col_professions.find_one({"name": payload["name"], "_id": {"$ne": oid}})
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe otra profesión con ese nombre")

    payload["updated_at"] = datetime.utcnow()

    col_professions.update_one({"_id": oid}, {"$set": payload})
    updated = col_professions.find_one({"_id": oid})
    return _serialize(updated)


# ---------- DELETE (Soft si hay dependencias) ----------
async def delete_profession_safe(id: str, request: Request):
    """
    Borrado seguro:
      - Si tiene servicios asociados -> desactivar (active=False).
      - Si no tiene -> eliminar definitivamente.
    Requiere admin o creador.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    oid = _to_oid(id)

    prof = col_professions.find_one({"_id": oid})
    if not prof:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    is_admin = bool(user.get("admin"))
    created_by = prof.get("created_by")
    is_owner = created_by is not None and str(created_by) == str(user.get("id"))

    if not (is_admin or is_owner):
        detail = "Solo el creador o un administrador puede eliminar esta profesión"
        if created_by is None:
            detail += " (este registro no tiene 'created_by', contacte a un administrador)"
        raise HTTPException(status_code=403, detail=detail)

    # Dependencias: aceptar ObjectId o string en id_profession
    deps = col_services.count_documents({
        "$or": [
            {"id_profession": oid},
            {"id_profession": str(oid)},
        ]
    })

    if deps > 0:
        col_professions.update_one(
            {"_id": oid},
            {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        return {
            "status": "deactivated",
            "message": "La profesión tiene servicios asociados; se desactivó en lugar de eliminarse.",
            "id": id,
            "linked_services": int(deps),
        }

    res = col_professions.delete_one({"_id": oid})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    return {
        "status": "deleted",
        "message": "Profesión eliminada definitivamente (no tenía servicios asociados).",
        "id": id,
        "linked_services": 0,
    }


# ---------- PIPELINE ENDPOINTS AUX ----------
async def professions_with_service_count(request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")
    return list(col_professions.aggregate(get_profession_with_service_count_pipeline()))

async def search_professions(q: str, skip: int, limit: int, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")
    return list(col_professions.aggregate(search_professions_pipeline(q, skip, limit)))

async def validate_profession_is_assigned(id: str, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")
    return list(col_professions.aggregate(validate_profession_is_assigned_pipeline(id)))


# ---- Alias para compatibilidad ----
async def get_professions(include_inactive: bool, request: Request):
    """Alias de get_all_professions para compatibilidad"""
    return await get_all_professions(include_inactive, request)





   





