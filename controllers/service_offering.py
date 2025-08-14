from fastapi import HTTPException
from bson import ObjectId
from utils.mongodb import get_collection
from models.service_offering import ServiceOffering

col = get_collection("service_offering")
prof_col = get_collection("profession")

def _to_out(doc: dict) -> dict | None:
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    doc["id_profession"] = str(doc["id_profession"])
    if "created_by" in doc and doc["created_by"] is not None:
        doc["created_by"] = str(doc["created_by"])
    return doc

async def list_services_active():
    cursor = col.find({"active": True})
    return [_to_out(d) for d in cursor]

async def create_service(service: ServiceOffering, *, actor_id: str):
    # validar profesión
    try:
        pid = ObjectId(service.id_profession)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id_profession")

    if not prof_col.find_one({"_id": pid, "active": True}):
        raise HTTPException(status_code=404, detail="Profession not found or inactive")

    # dueño
    try:
        owner = ObjectId(actor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid actor id")

    res = col.insert_one({
        "id_profession": pid,
        "description": service.description,
        "estimated_price": service.estimated_price,
        "estimated_duration": service.estimated_duration,
        "active": service.active,
        "created_by": owner,
    })
    return _to_out(col.find_one({"_id": res.inserted_id}))

# mantenemos firma con is_admin para no romper rutas, pero NO se usa (solo dueño puede)
async def update_service(id: str, service: ServiceOffering, *, actor_id: str, is_admin: bool):
    try:
        _id = ObjectId(id)
        pid = ObjectId(service.id_profession)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id or id_profession")

    if not prof_col.find_one({"_id": pid, "active": True}):
        raise HTTPException(status_code=404, detail="Profession not found or inactive")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Service not found")

    # solo dueño
    try:
        actor = ObjectId(actor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid actor id")
    if current.get("created_by") != actor:
        raise HTTPException(status_code=403, detail="Not owner of this service")

    col.update_one({"_id": _id}, {"$set": {
        "id_profession": pid,
        "description": service.description,
        "estimated_price": service.estimated_price,
        "estimated_duration": service.estimated_duration,
        "active": service.active,
    }})
    return _to_out(col.find_one({"_id": _id}))

# mantenemos firma con is_admin para no romper rutas, pero NO se usa (solo dueño puede)
async def delete_service(id: str, *, actor_id: str, is_admin: bool):
    try:
        _id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Service not found")

    # solo dueño
    try:
        actor = ObjectId(actor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid actor id")
    if current.get("created_by") != actor:
        raise HTTPException(status_code=403, detail="Not owner of this service")

    col.update_one({"_id": _id}, {"$set": {"active": False}})
    return {"ok": True}






