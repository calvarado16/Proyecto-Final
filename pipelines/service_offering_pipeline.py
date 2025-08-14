# pipelines/service_offering.py
from bson import ObjectId

def list_services_pipeline(*, include_inactive: bool = False) -> list:
    match_stage = {"$match": {}} if include_inactive else {"$match": {"active": True}}
    return [
        match_stage,
        {"$lookup": {
            "from": "profession",
            "localField": "id_profession",
            "foreignField": "_id",
            "as": "profession"
        }},
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "id_profession": {"$toString": "$id_profession"},
            "profession_name": "$profession.name",
            "description": 1,
            "estimated_price": 1,
            "estimated_duration": 1,
            "active": 1
        }},
        {"$sort": {"profession_name": 1, "description": 1}}
    ]

def service_by_id_pipeline(service_id: str) -> list:
    return [
        {"$match": {"_id": ObjectId(service_id)}},
        {"$lookup": {
            "from": "profession",
            "localField": "id_profession",
            "foreignField": "_id",
            "as": "profession"
        }},
        {"$unwind": {"path": "$profession", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "id_profession": {"$toString": "$id_profession"},
            "profession_name": "$profession.name",
            "description": 1,
            "estimated_price": 1,
            "estimated_duration": 1,
            "active": 1
        }}
    ]

