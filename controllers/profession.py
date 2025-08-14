# controllers/profession.py
from fastapi import HTTPException, Request
from bson import ObjectId
from utils.mongodb import get_collection
from models.profession import Profession

# ⬇️ importa los pipelines
from pipelines.profession_pipelines import (
    get_all_professions_pipeline,
    get_profession_with_service_count_pipeline,
    search_professions_pipeline,
)
from pipelines.profession_type_pipelines import (
    validate_profession_is_assigned_pipeline,
)

col_professions = get_collection("profession")

# ---------- CREATE ----------
async def create_profession(prof: Profession, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    exists = col_professions.find_one({"name": prof.name})
    if exists:
        raise HTTPException(status_code=400, detail="La profesión ya existe")

    data = prof.model_dump()
    data.pop("id", None)
    data["created_by"] = user.get("id")

    res = col_professions.insert_one(data)
    data["id"] = str(res.inserted_id)
    data.pop("_id", None)
    return data

# ---------- READ LIST (via pipeline) ----------
async def get_all_professions(include_inactive: bool, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")

    pipeline = get_all_professions_pipeline(
        skip=0, limit=10_000, include_inactive=include_inactive
    )
    items = list(col_professions.aggregate(pipeline))
    return items

# ---------- READ ONE ----------
async def get_profession_by_id(id: str, request: Request):
    if not getattr(request.state, "user", None):
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    doc = col_professions.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Profession no encontrada")

    doc["id"] = str(doc["_id"]); doc.pop("_id", None)
    return doc

# ---------- UPDATE ----------
async def update_profession(id: str, prof: Profession, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    current = col_professions.find_one({"_id": oid})
    if not current:
        raise HTTPException(status_code=404, detail="Profession no encontrada")

    is_admin = bool(user.get("admin"))
    is_owner = str(current.get("created_by")) == str(user.get("id"))
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Solo el creador o un administrador puede actualizar esta profesión")

    payload = prof.model_dump(exclude_unset=True)
    payload.pop("id", None)
    payload.pop("created_by", None)

    if "name" in payload:
        dup = col_professions.find_one({"name": payload["name"], "_id": {"$ne": oid}})
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe otra profesión con ese nombre")

    col_professions.update_one({"_id": oid}, {"$set": payload})
    updated = col_professions.find_one({"_id": oid})
    updated["id"] = str(updated["_id"]); updated.pop("_id", None)
    return updated

# ---------- DELETE (con validación opcional) ----------
async def delete_profession_safe(id: str, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    prof = col_professions.find_one({"_id": oid})
    if not prof:
        raise HTTPException(status_code=404, detail="Profession no encontrada")

    is_admin = bool(user.get("admin"))
    is_owner = str(prof.get("created_by")) == str(user.get("id"))
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Solo el creador o un administrador puede eliminar esta profesión")


    col_professions.delete_one({"_id": oid})
    return {"deleted": True, "id": id}

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


   





