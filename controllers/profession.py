import os
import logging
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from fastapi import HTTPException
from dotenv import load_dotenv
from bson.objectid import ObjectId

from models.profession import Profession

load_dotenv()

DB = os.getenv("MONGO_DB_NAME")
URI = os.getenv("URI")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_collection(uri, col):
    client = MongoClient(
        uri,
        server_api=ServerApi("1"),
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    client.admin.command("ping")
    return client[DB][col]

# ===============================
# Crear una profesión
# ===============================
async def create_profession(profession: Profession) -> Profession:
    coll = get_collection(URI, "professions")
    try:
        new_doc = profession.model_dump(exclude={"id"})
        result = coll.insert_one(new_doc)
        profession.id = str(result.inserted_id)
        return profession
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# Obtener todas las profesiones
# ===============================
async def get_all_professions():
    coll = get_collection(URI, "professions")
    professions = list(coll.find())
    for p in professions:
        p["id"] = str(p["_id"])
        del p["_id"]
    return professions

# ===============================
# Obtener profesión por ID
# ===============================
async def get_profession_by_id(profession_id: str) -> Profession:
    coll = get_collection(URI, "professions")
    if not ObjectId.is_valid(profession_id):
        raise HTTPException(status_code=400, detail="ID de profesion invalido")

    doc = coll.find_one({"_id": ObjectId(profession_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="No se encontro profesion")

    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return Profession(**doc)

# ===============================
# Actualizar una profesión
# ===============================
async def update_profession(profession_id: str, profession: Profession) -> dict:
    coll = get_collection(URI, "professions")
    if not ObjectId.is_valid(profession_id):
        raise HTTPException(status_code=400, detail="ID de profesion invalido")

    updated_data = profession.model_dump(exclude={"id"})
    result = coll.update_one({"_id": ObjectId(profession_id)}, {"$set": updated_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No se encontro profesion")

    return {"message": "Se actualizo la profesion de manera exitosa"}

# ===============================
# Eliminar una profesión
# ===============================
async def delete_profession(profession_id: str) -> dict:
    coll = get_collection(URI, "professions")
    if not ObjectId.is_valid(profession_id):
        raise HTTPException(status_code=400, detail="ID de profesion invalido")

    result = coll.delete_one({"_id": ObjectId(profession_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se encontro la profesion")

    return {"message": "Se borro la profesion de manera exitosa"}




