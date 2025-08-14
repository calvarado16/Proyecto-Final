from bson import ObjectId

def get_profession_with_service_count_pipeline() -> list:
    """
    Lista todas las profesiones con número de servicios asociados.
    """
    return [
        {"$addFields": {"id": {"$toString": "$_id"}}},
        {"$lookup": {
            "from": "service_offering",
            "localField": "id",
            "foreignField": "id_profession",
            "as": "services"
        }},
        {"$group": {
            "_id": {
                "id": "$id",
                "name": "$name",
                "active": "$active"
            },
            "number_of_services": {"$sum": {"$size": "$services"}}
        }},
        {"$project": {
            "_id": 0,
            "id": "$_id.id",
            "name": "$_id.name",
            "active": "$_id.active",
            "number_of_services": 1
        }}
    ]

def get_all_professions_pipeline(skip: int = 0, limit: int = 10, include_inactive: bool = False) -> list:
    """
    Devuelve todas las profesiones con control de estado y paginación.
    """
    match_stage = {} if include_inactive else {"active": True}
    return [
        {"$match": match_stage},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "name": "$name",
            "active": "$active"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]

def search_professions_pipeline(search_term: str, skip: int = 0, limit: int = 10) -> list:
    """
    Busca profesiones por nombre (case-insensitive).
    """
    return [
        {"$match": {
            "name": {"$regex": search_term, "$options": "i"},
            "active": True
        }},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "name": "$name",
            "active": "$active"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]
