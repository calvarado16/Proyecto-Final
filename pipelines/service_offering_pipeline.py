from bson import ObjectId

def list_services_pipeline(*, include_inactive: bool = False,
                           only_active_profession: bool = False) -> list:
    """
    Lista servicios con su profesión relacionada.
    - include_inactive: incluye servicios inactivos si True.
    - only_active_profession: filtra también profesiones inactivas si True.
    Soporta id_profession guardado como ObjectId o como string.
    """
    match_stage = {"$match": {}} if include_inactive else {"$match": {"active": True}}

    # Lookup que compara como string para evitar problemas de tipo
    lookup_pipeline = [
        {"$match": {
            "$expr": {
                "$eq": [
                    {"$toString": "$_id"},
                    {"$toString": "$$pid"}
                ]
            }
        }},
        {"$project": {"_id": 1, "name": 1, "active": 1}}
    ]
    if only_active_profession:
        lookup_pipeline.insert(1, {"$match": {"active": True}})

    return [
        match_stage,
        {"$lookup": {
            "from": "profession",
            "let": {"pid": "$id_profession"},
            "pipeline": lookup_pipeline,
            "as": "profession"
        }},
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "id_profession": {"$toString": "$id_profession"},
            "profession": {
                "id": {"$toString": "$profession._id"},
                "name": "$profession.name",
                "active": "$profession.active",
            },
            "description": 1,
            "estimated_price": 1,
            "estimated_duration": 1,
            "active": 1
        }},
        {"$sort": {"profession.name": 1, "description": 1}}
    ]


def service_by_id_pipeline(service_id: str) -> list:
    """
    Obtiene un servicio por id con su profesión relacionada.
    Soporta id_profession como ObjectId o string.
    """
    return [
        {"$match": {"_id": ObjectId(service_id)}},
        {"$lookup": {
            "from": "profession",
            "let": {"pid": "$id_profession"},
            "pipeline": [
                {"$match": {
                    "$expr": {
                        "$eq": [
                            {"$toString": "$_id"},
                            {"$toString": "$$pid"}
                        ]
                    }
                }},
                {"$project": {"_id": 1, "name": 1, "active": 1}}
            ],
            "as": "profession"
        }},
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "id_profession": {"$toString": "$id_profession"},
            "profession": {
                "id": {"$toString": "$profession._id"},
                "name": "$profession.name",
                "active": "$profession.active",
            },
            "description": 1,
            "estimated_price": 1,
            "estimated_duration": 1,
            "active": 1
        }}
    ]


