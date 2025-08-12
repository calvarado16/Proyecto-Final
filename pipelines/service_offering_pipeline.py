from bson import ObjectId

def get_full_service_offering_pipeline(service_id: str) -> list:
    """
    Devuelve un servicio con detalles del profesional, reseñas y reservas.
    Maneja casos donde id_profesional no es un ObjectId válido.
    """
    return [
        {"$match": {"_id": ObjectId(service_id)}},

        # Convertir id_profesional a ObjectId de forma segura
        {"$addFields": {
            "id_profesional_obj": {
                "$convert": {
                    "input": "$id_profesional",
                    "to": "objectId",
                    "onError": None,
                    "onNull": None
                }
            }
        }},

        # Filtrar si la conversión falló
        {"$match": {
            "id_profesional_obj": {"$ne": None}
        }},

        # Profesional asociado
        {"$lookup": {
            "from": "users",
            "localField": "id_profesional_obj",
            "foreignField": "_id",
            "as": "profesional"
        }},
        {"$unwind": "$profesional"},

        # Reviews asociadas
        {"$lookup": {
            "from": "reviews",
            "localField": "_id",
            "foreignField": "id_service_offering",
            "as": "reviews"
        }},

        # Reservas asociadas
        {"$lookup": {
            "from": "reservation_service",
            "localField": "_id",
            "foreignField": "id_service_offering",
            "as": "reservations"
        }},

        # Proyección final
        {"$project": {
            "_id": 0,
            "id": {"$toString": "$_id"},
            "nombre": 1,
            "descripcion": 1,
            "precio": 1,
            "duracion_min": 1,
            "profesional": {
                "nombre": "$profesional.name",
                "email": "$profesional.email"
            },
            "reviews": 1,
            "reservations": 1
        }}
    ]

