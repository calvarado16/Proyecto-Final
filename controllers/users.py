import base64
import os 
import json 
import logging
import firebase_admin
from pymongo import MongoClient
import requests
 
from firebase_admin import credentials
from firebase_admin import auth as firebase_auth 

from fastapi import HTTPException
from dotenv import load_dotenv 
from pymongo.server_api import ServerApi

from models.login import Login
from models.users import User

from utils.security import create_jwt_token


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DB = os.getenv("MONGO_DB_NAME")
URI = os.getenv("URI")

#cred = credentials.Certificate("secrets/taxfixer-secrets.json")
#firebase_admin.initialize_app(cred)

def initialize_firebase():
    if firebase_admin._apps:
        return
    
    try: 
        firebase_creds_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")

        if firebase_creds_base64:
            firebase_creds_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
            firebase_creds = json.loads(firebase_creds)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with environment variable credentials")
    
        else: 
            cred = credentials.Certificate("secrets/taxfixer-secrets.json")  
            firebase_admin.initialize_app(cred)
            logger.info("Frebase initialize with JSON file")  
    
    except Exception as e:
        logger.error(f"Failed to initialized Firebase: {e}")
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")
    
initialize_firebase()    
    
    
    
def get_collection(uri, col):
    client = MongoClient(
        uri,  
        server_api=ServerApi("1"),
        tls=True,
        tlsAllowInvalidCertificates=True
    )    
    client.admin.command("ping")
    return client[DB][col]

async def create_user(user: User) -> User: 
    user_record = {}
    try:
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password
        )
    except Exception as e: 
        logger.warning(e)
        raise HTTPException(
            status_code=400, 
            detail="Error al registrar usuario al firebase"
        )
    
    try: 
        coll = get_collection(URI, "users")
        user_dict = user.model_dump(exclude={"id", "password"})
        inserted = coll.insert_one(user_dict)
        user.id = str(inserted.inserted_id)
        return user
    except Exception as e: 
        firebase_auth.delete_user(user_record.uid)
        logger.error("Error creating user", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating user")
    
async def login(user: Login):
    api_key = os.getenv("FIREBASE_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": user.email, 
        "password": user.password, 
        "returnSecureToken": True
    } 
    response = requests.post(url, json=payload)
    response_data = response.json()
    
    if "error" in response_data:
        raise HTTPException(
            status_code=400, 
            detail="Error al autenticar usuario."
        ) 
    
    coll = get_collection(URI, "users")
    users_info = coll.find_one({"email": user.email}) 
    logger.info(users_info["name"])
    
    return {
        "message": "Usuario Autenticado correctamente",
        "idToken": create_jwt_token(
            id=str(users_info["_id"]),
            firstname=users_info["name"],
            lastname=users_info["lastname"],
            email=users_info["email"],
            active=users_info["active"],
            profesional=users_info["profesional"],
            admin=users_info["admin"]
        )
    }

