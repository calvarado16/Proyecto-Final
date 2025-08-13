import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

# Lee distintos nombres de variables de entorno para ser compatible
DB = (
    os.getenv("MONGO_DB_NAME")
    or os.getenv("DATABASE_NAME")
    or os.getenv("DB_NAME")
)
URI = (
    os.getenv("MONGODB_URI")   # recomendado para Atlas/Railway
    or os.getenv("MONGO_URI")
    or os.getenv("MONGO_URL")
    or os.getenv("URI")
)

if not DB:
    raise ValueError("Database name not found. Set MONGO_DB_NAME / DATABASE_NAME / DB_NAME.")
if not URI:
    raise ValueError("MongoDB URI not found. Set MONGODB_URI / MONGO_URI / MONGO_URL / URI.")

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Devuelve un cliente MongoDB singleton."""
    global _client
    if _client is None:
        _client = MongoClient(
            URI,
            server_api=ServerApi("1"),
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=10_000,  # 10s
        )
    return _client


def get_collection(col: str):
    """Obtiene una colección de la BD configurada."""
    return get_mongo_client()[DB][col]


def test_connection() -> bool:
    """Hace ping a Mongo para verificar conectividad."""
    try:
        get_mongo_client().admin.command("ping")
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False


# Alias por compatibilidad con código que importe t_connection
t_connection = test_connection
