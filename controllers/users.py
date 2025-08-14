# controllers/users.py
import os
import json
import logging
import firebase_admin
import requests
import base64
from fastapi import HTTPException
from firebase_admin import credentials, auth as firebase_auth
from dotenv import load_dotenv

from models.users import User
from models.login import Login

from utils.security import create_jwt_token
from utils.mongodb import get_collection

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_firebase():
    """Inicializa Firebase una sola vez, desde BASE64 o archivo local."""
    if firebase_admin._apps:
        return
    try:
        firebase_creds_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
        if firebase_creds_base64:
            firebase_creds_json = base64.b64decode(firebase_creds_base64).decode("utf-8")
            firebase_creds = json.loads(firebase_creds_json)
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with environment variable credentials")
        else:
            # Fallback local (asegúrate de que el archivo exista en ese path)
            cred = credentials.Certificate("secrets/dulceria-secret.json")
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with JSON file")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")


initialize_firebase()


async def create_user(user: User) -> User:
    """
    Crea el usuario en Firebase (si no existe) y luego lo inserta en Mongo.
    Devuelve el modelo User (sin password en claro, enmascarado).
    """
    # 0) Validar duplicado en Mongo
    coll = get_collection("users")
    if coll.find_one({"email": user.email}):
        raise HTTPException(status_code=409, detail="Email ya registrado en la base de datos")

    # 1) Verificar si ya existe en Firebase
    fb_user = None
    try:
        fb_user = firebase_auth.get_user_by_email(user.email)
        logger.info("Email ya existe en Firebase, se reutilizará el UID.")
    except Exception:
        # No existe en Firebase o error transitorio: continuamos y tratamos de crearlo
        fb_user = None

    created_in_firebase = False
    try:
        # 2) Crear en Firebase si no existe
        if not fb_user:
            fb_user = firebase_auth.create_user(
                email=user.email,
                password=user.password,
            )
            created_in_firebase = True

    except Exception as e:
        logger.warning(f"[FIREBASE] create_user error: {repr(e)}")
        # Error claro al cliente
        raise HTTPException(
            status_code=400,
            detail=f"Error al registrar usuario en Firebase: {str(e)}"
        )

    # 3) Insertar en Mongo (sin password) y devolver objeto User
    try:
        new_user = User(
            name=user.name,
            lastname=user.lastname,
            email=user.email,
            password=user.password  # se enmascara en la respuesta
        )

        user_dict = new_user.model_dump(exclude={"id", "password"})
        # Respetar defaults del modelo: active=True, admin=False
        if "active" not in user_dict:
            user_dict["active"] = True
        if "admin" not in user_dict:
            user_dict["admin"] = False

        inserted = coll.insert_one(user_dict)
        new_user.id = str(inserted.inserted_id)
        new_user.password = "*********"  # Enmascarar

        return new_user

    except Exception as e:
        # Rollback en Firebase solo si lo creamos en este request
        if created_in_firebase and fb_user is not None:
            try:
                firebase_auth.delete_user(fb_user.uid)
            except Exception:
                pass
        logger.error(f"Error creating user in MongoDB: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def login(user: Login) -> dict:
    """
    Autentica con Firebase (REST) y devuelve tu JWT propio en el campo `idToken`,
    manteniendo tu estructura actual.
    """
    api_key = os.getenv("FIREBASE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY no configurada")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": user.email,
        "password": user.password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()
    except Exception as e:
        logger.error("Error calling Firebase Identity", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error comunicando con Firebase: {str(e)}")

    if "error" in response_data:
        raise HTTPException(
            status_code=400,
            detail="Error al autenticar usuario"
        )

    coll = get_collection("users")
    user_info = coll.find_one({"email": user.email})

    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado en la base de datos"
        )

    # Mantengo tu estructura: el JWT propio va en el campo `idToken`
    return {
        "message": "Usuario Autenticado correctamente",
        "idToken": create_jwt_token(
            user_info.get("name", ""),
            user_info.get("lastname", ""),
            user_info["email"],
            user_info.get("active", True),
            user_info.get("admin", False),
            str(user_info["_id"])
        )
    }

