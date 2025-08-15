# controllers/profession.py
from fastapi import HTTPException
from bson import ObjectId
from utils.mongodb import get_collection


async def delete_profession_safe(id: str, request=None) -> dict:
    """
    Si la profesión tiene servicios asociados en 'service_offering',
    se desactiva (soft delete). Si no, se elimina definitivamente.
    """
    prof_coll = get_collection("profession")
    serv_coll = get_collection("service_offering")

    # Validar ObjectId
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")

    # ¿Existe la profesión?
    prof = prof_coll.find_one({"_id": oid})
    if not prof:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    # Verificar dependencias (servicios relacionados)
    deps = serv_coll.count_documents({"id_profession": oid})

    if deps > 0:
        # Soft delete: marcar inactiva si hay dependencias
        prof_coll.update_one({"_id": oid}, {"$set": {"active": False}})
        return {
            "message": "La profesión está en uso, se desactivó.",
            "softDisabled": True,
            "dependencies": int(deps),
        }

    # Sin dependencias: eliminación definitiva
    res = prof_coll.delete_one({"_id": oid})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    return {
        "message": "Profesión eliminada correctamente.",
        "softDisabled": False,
    }





