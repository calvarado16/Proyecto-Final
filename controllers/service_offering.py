from fastapi import HTTPException
from bson import ObjectId
from utils.mongodb import get_collection
from models.service_offering import ServiceOffering

col = get_collection("service_offering")
prof_col = get_collection("profession")

# -----------------------------
# Pipelines embebidos
# -----------------------------
def _project_stage():
    return {
        "$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "id_profession": {"$toString": "$id_profession"},
            "profession_name": "$profession.name",
            "description": 1,
            "estimated_price": 1,
            "estimated_duration": 1,
            "active": 1,
            "created_by": {"$toString": "$created_by"},
        }
    }

def _list_pipeline(*, active_only: bool = True, owner_id: str | None = None):
    match: dict = {}
    if active_only:
        match["active"] = True
    if owner_id:
        try:
            match["created_by"] = ObjectId(owner_id)
        except Exception:
            pass

    return [
        {"$match": match},
        {
            "$lookup": {
                "from": "profession",
                "localField": "id_profession",
                "foreignField": "_id",
                "as": "profession",
            }
        },
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        _project_stage(),
    ]

def _by_id_pipeline(service_id: str):
    return [
        {"$match": {"_id": ObjectId(service_id)}},
        {
            "$lookup": {
                "from": "profession",
                "localField": "id_profession",
                "foreignField": "_id",
                "as": "profession",
            }
        },
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        _project_stage(),
    ]


# -----------------------------
# Helpers
# -----------------------------
def _ensure_objectid(s: str, name: str = "id") -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {name}")

def _get_by_id_agg_str(service_id: str) -> dict:
    """Devuelve 1 service offering con lookup y proyección usando aggregate."""
    pipe = _by_id_pipeline(service_id)
    docs = list(col.aggregate(pipe))
    if not docs:
        raise HTTPException(status_code=404, detail="Service not found")
    return docs[0]


# -----------------------------
# Endpoints (lógica)
# -----------------------------
async def list_services_active():
    """Mantiene tu firma original pero ahora usa aggregate + lookup."""
    pipe = _list_pipeline(active_only=True)
    return list(col.aggregate(pipe))

async def create_service(service: ServiceOffering, *, actor_id: str):
    # validar profesión
    pid = _ensure_objectid(service.id_profession, "id_profession")

    if not prof_col.find_one({"_id": pid, "active": True}):
        raise HTTPException(status_code=404, detail="Profession not found or inactive")

    # dueño
    owner = _ensure_objectid(actor_id, "actor id")

    res = col.insert_one({
        "id_profession": pid,
        "description": service.description,
        "estimated_price": service.estimated_price,
        "estimated_duration": service.estimated_duration,
        "active": service.active,
        "created_by": owner,
    })

    # devolver ya con lookup/proyección
    return _get_by_id_agg_str(str(res.inserted_id))

# mantenemos firma con is_admin para no romper rutas, pero NO se usa (solo dueño puede)
async def update_service(id: str, service: ServiceOffering, *, actor_id: str, is_admin: bool):
    _id = _ensure_objectid(id, "id")
    pid = _ensure_objectid(service.id_profession, "id_profession")

    if not prof_col.find_one({"_id": pid, "active": True}):
        raise HTTPException(status_code=404, detail="Profession not found or inactive")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Service not found")

    actor = _ensure_objectid(actor_id, "actor id")
    if current.get("created_by") != actor:
        raise HTTPException(status_code=403, detail="Not owner of this service")

    col.update_one({"_id": _id}, {"$set": {
        "id_profession": pid,
        "description": service.description,
        "estimated_price": service.estimated_price,
        "estimated_duration": service.estimated_duration,
        "active": service.active,
    }})

    return _get_by_id_agg_str(id)

# mantenemos firma con is_admin para no romper rutas, pero NO se usa (solo dueño puede)
async def delete_service(id: str, *, actor_id: str, is_admin: bool):
    _id = _ensure_objectid(id, "id")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Service not found")

    actor = _ensure_objectid(actor_id, "actor id")
    if current.get("created_by") != actor:
        raise HTTPException(status_code=403, detail="Not owner of this service")

    col.update_one({"_id": _id}, {"$set": {"active": False}})
    return {"ok": True}







