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
from utils.mongodb import get_collection  

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
            # ⚠️ Asegúrate que el nombre del archivo sea correcto (taskfixer, no 'taxfixer')
            cred = credentials.Certificate("secrets/taskfixer-secrets.json")
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with secrets file")
    except Exception as e:
        logger.error("Failed to initialize Firebase: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")


initialize_firebase()


async def create_user(user: User) -> dict:
    """
    Crea el usuario en Firebase y lo guarda en Mongo.
    Devuelve: { token, user } (SIN password).
    """
    coll = get_collection("users")

    # Evita duplicado por email (opcional pero recomendado)
    if coll.find_one({"email": user.email}):
        raise HTTPException(status_code=409, detail="Email ya registrado")

    # 1) Crear cuenta en Firebase Auth
    try:
        display_name = f"{getattr(user, 'name', '')} {getattr(user, 'lastname', '')}".strip()
        fb_rec = firebase_auth.create_user(
            email=user.email,
            password=user.password,
            display_name=display_name,
            disabled=False,
        )
    except Exception as e:
        logger.warning("Firebase create_user error: %s", e)
        raise HTTPException(status_code=400, detail="Error al registrar usuario en Firebase")

    # 2) Guardar en Mongo (excluye password) + defaults + firebase_uid
    try:
        doc = user.model_dump(exclude={"id", "password"})
        doc.setdefault("active", True)
        doc.setdefault("admin", False)
        doc.setdefault("profesional", False)
        doc["firebase_uid"] = fb_rec.uid

        res = coll.insert_one(doc)
        user_id = str(res.inserted_id)

        # 3) Emitir JWT propio
        first = doc.get("name", "")  # tu modelo usa 'name', no 'firstname'
        token = create_jwt_token(
            id=user_id,
            firstname=first,
            lastname=doc.get("lastname", ""),
            email=doc["email"],
            active=doc.get("active", True),
            admin=doc.get("admin", False),
        )

        # 4) Respuesta saneada (sin password, con id en str)
        user_out = {**doc, "id": user_id}
        user_out.pop("_id", None)

        return {"token": token, "user": user_out}

    except Exception:
        # Rollback en Firebase si la inserción en Mongo falla
        try:
            firebase_auth.delete_user(fb_rec.uid)
        except Exception:
            pass
        logger.error("Error creating user in MongoDB", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating usuario")


async def login(login_data: Login) -> dict:
    """
    Sign-in contra Firebase Identity y devuelve JWT propio + user de Mongo.
    """
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

    # Cargar información del usuario desde Mongo
    coll = get_collection("users")
    u = coll.find_one({"email": login_data.email})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")

    first = u.get("name", "")
    token = create_jwt_token(
        id=str(u.get("_id")),
        firstname=first,
        lastname=u.get("lastname", ""),
        email=u.get("email"),
        active=u.get("active", True),
        admin=u.get("admin", False),
    )

    user_out = {
        "id": str(u.get("_id")),
        "name": first,
        "lastname": u.get("lastname", ""),
        "email": u.get("email"),
        "active": u.get("active", True),
        "admin": u.get("admin", False),
        "profesional": u.get("profesional", False),
        "firebase_uid": u.get("firebase_uid"),
    }

    return {"message": "Usuario Autenticado correctamente", "token": token, "user": user_out}
