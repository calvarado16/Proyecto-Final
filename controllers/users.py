# controllers/users.py
import os
import json
import base64
import logging
import requests
import firebase_admin

from fastapi import HTTPException
from dotenv import load_dotenv
from firebase_admin import credentials
from firebase_admin import auth as firebase_auth

from models.login import Login
from models.users import User
from utils.security import create_jwt_token
from utils.mongodb import get_collection  # usa el helper unificado

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_firebase() -> None:
    """Inicializa Firebase una sola vez, tomando credenciales del .env (BASE64) o de un archivo local."""
    if firebase_admin._apps:
        return
    try:
        firebase_creds_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
        if firebase_creds_base64:
            firebase_creds_json = base64.b64decode(firebase_creds_base64).decode("utf-8")
            cred = credentials.Certificate(json.loads(firebase_creds_json))
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with env BASE64 credentials")
        else:
            # fallback a archivo local si lo usas en desarrollo
            cred = credentials.Certificate("secrets/taxfixer-secrets.json")
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with secrets file")
    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")


initialize_firebase()


async def create_user(user: User) -> User:
    """Crea el usuario en Firebase y lo guarda en Mongo. Si Mongo falla, hace rollback en Firebase."""
    user_record = None
    try:
        # Crear cuenta en Firebase Auth
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password,
        )
    except Exception as e:
        logger.warning("Firebase create_user error: %s", e)
        raise HTTPException(status_code=400, detail="Error al registrar usuario en Firebase")

    try:
        # Guardar en Mongo (excluimos id/password del documento)
        coll = get_collection("users")
        user_doc = user.model_dump(exclude={"id", "password"})
        inserted = coll.insert_one(user_doc)
        user.id = str(inserted.inserted_id)
        return user
    except Exception:
        # Rollback en Firebase si la inserción en Mongo falla
        try:
            if user_record and getattr(user_record, "uid", None):
                firebase_auth.delete_user(user_record.uid)
        except Exception:
            pass
        logger.error("Error creating user in MongoDB", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating user")


async def login(login_data: Login) -> dict:
    """Hace sign-in contra Firebase Identity y devuelve un JWT propio con los claims del usuario en Mongo."""
    api_key = os.getenv("FIREBASE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY no configurada")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": login_data.email,
        "password": login_data.password,
        "returnSecureToken": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
    except Exception:
        logger.error("Error calling Firebase Identity", exc_info=True)
        raise HTTPException(status_code=502, detail="Error comunicando con Firebase")

    if "error" in data:
        # credenciales inválidas
        raise HTTPException(status_code=400, detail="Error al autenticar usuario.")

    # Buscar información del usuario en tu Mongo
    coll = get_collection("users")
    user_info = coll.find_one({"email": login_data.email})
    if not user_info:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")

    return {
        "message": "Usuario Autenticado correctamente",
        "idToken": create_jwt_token(
            id=str(user_info.get("_id")),
            firstname=user_info.get("name"),
            lastname=user_info.get("lastname"),
            email=user_info.get("email"),
            active=user_info.get("active", True),
            profesional=user_info.get("profesional", False),
            admin=user_info.get("admin", False),
        ),
    }

