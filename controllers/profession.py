from fastapi import HTTPException
from bson import ObjectId
from utils.mongodb import get_collection
from models.profession import Profession

col = get_collection("profession")

def _to_out(doc):
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    if "created_by" in doc and doc["created_by"] is not None:
        doc["created_by"] = str(doc["created_by"])
    return doc

async def list_professions_active():
    return [_to_out(d) for d in col.find({"active": True})]

async def create_profession(prof: Profession, *, actor_id: str):
    try:
        owner = ObjectId(actor_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid actor id")

    res = col.insert_one({
        "name": prof.name,
        "active": prof.active,
        "created_by": owner
    })
    return _to_out(col.find_one({"_id": res.inserted_id}))

async def update_profession(id: str, prof: Profession, *, actor_id: str, is_admin: bool):
    try:
        _id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid id")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Profession not found")

    # Solo dueño o admin
    if not is_admin:
        try:
            actor = ObjectId(actor_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid actor id")
        if current.get("created_by") != actor:
            raise HTTPException(status_code=403, detail="Not owner of this profession")

    col.update_one({"_id": _id}, {"$set": {
        "name": prof.name,
        "active": prof.active
    }})
    return _to_out(col.find_one({"_id": _id}))

async def delete_profession(id: str, *, actor_id: str, is_admin: bool):
    try:
        _id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid id")

    current = col.find_one({"_id": _id})
    if not current:
        raise HTTPException(status_code=404, detail="Profession not found")

    if not is_admin:
        try:
            actor = ObjectId(actor_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid actor id")
        if current.get("created_by") != actor:
            raise HTTPException(status_code=403, detail="Not owner of this profession")

    col.update_one({"_id": _id}, {"$set": {"active": False}})
    return {"ok": True}





