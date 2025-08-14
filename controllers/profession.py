# controllers/profession.py
from fastapi import HTTPException, status, Request
from bson import ObjectId
from utils.mongodb import get_collection
from models.profession import Profession

col_professions = get_collection("profession")

def _oid_or_str(v: str):
    try:
        return ObjectId(v)
    except Exception:
        return v

# ---------- CREATE ----------
async def create_profession(prof: Profession, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    # 👇 CAMBIO: description -> name
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

# ---------- UPDATE ----------
async def update_profession(id: str, prof: Profession, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    oid = ObjectId(id)
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

    # 👇 (opcional) validar duplicado por name, excluyendo el mismo documento
    if "name" in payload:
        dup = col_professions.find_one({"name": payload["name"], "_id": {"$ne": oid}})
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe otra profesión con ese nombre")

    col_professions.update_one({"_id": oid}, {"$set": payload})
    updated = col_professions.find_one({"_id": oid})
    updated["id"] = str(updated["_id"]); updated.pop("_id", None)
    return updated

# ---------- DELETE ----------
async def delete_profession_safe(id: str, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")

    oid = ObjectId(id)
    prof = col_professions.find_one({"_id": oid})
    if not prof:
        raise HTTPException(status_code=404, detail="Profession no encontrada")

    is_admin = bool(user.get("admin"))
    is_owner = str(prof.get("created_by")) == str(user.get("id"))
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Solo el creador o un administrador puede eliminar esta profesión")

    col_professions.delete_one({"_id": oid})
    return {"deleted": True, "id": id}


   





