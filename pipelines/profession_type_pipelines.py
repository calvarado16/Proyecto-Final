from bson import ObjectId

def validate_profession_is_assigned_pipeline(id: str) -> list:
    """
    Verifica si una profesión tiene servicios asociados.
    Útil para evitar eliminar profesiones en uso.
    """
    return [
        {"$match": {"_id": ObjectId(id)}},
        {"$addFields": {"id": {"$toString": "$_id"}}},
        {"$lookup": {
            "from": "service_offering",
            "localField": "id",
            "foreignField": "id_profession",
            "as": "services"
        }},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "name": "$name",
            "active": "$active",
            "number_of_services": {"$size": "$services"}
        }}
    ]
