import os
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from models.profession import Profession
from utils.mongodb import get_collection
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

router = APIRouter(tags=["Public Profession"])

# Obtener la colección directamente (sin pasar MONGO_URI)
profession_coll = get_collection("profession")

@router.get("/public/professions", response_model=List[Profession])
async def get_public_professions(
    name: Optional[str] = Query(None, description="Buscar por nombre parcial de la profesión"),
    category: Optional[str] = Query(None, description="Filtrar por categoría exacta")
):
    """
    Endpoint público para consultar profesiones por nombre y/o categoría.
    No requiere autenticación.
    """
    try:
        query = {}

        if name:
            query["name"] = {"$regex": name, "$options": "i"}

        if category:
            query["category"] = category

        results = []
        for doc in profession_coll.find(query):
            doc["id"] = str(doc["_id"])
            results.append(Profession(**doc))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener profesiones: {e}")


