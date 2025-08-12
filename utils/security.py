import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from jwt import PyJWTError
from functools import wraps

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
security = HTTPBearer()

# ========================
# Crear JWT Token
# ========================
def create_jwt_token(
    firstname: str,
    lastname: str,
    email: str,
    active: bool,
    admin: bool,
    profesional: bool,
    id: str
):
    expiration = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(
        {
            "id": id,
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "active": active,
            "admin": admin,
            "profesional": profesional,
            "exp": expiration,
            "iat": datetime.utcnow()
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

# ========================
# Validar usuario autenticado
# ========================
def validateuser(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        try:
            schema, token = authorization.split()
            if schema.lower() != "bearer":
                raise HTTPException(status_code=400, detail="Invalid auth schema")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if payload.get("email") is None:
                raise HTTPException(status_code=401, detail="Token Invalid")
            if datetime.utcfromtimestamp(payload.get("exp")) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Expired token")
            if not payload.get("active"):
                raise HTTPException(status_code=401, detail="Inactive user")

            request.state.id = payload.get("id")
            request.state.email = payload.get("email")
            request.state.firstname = payload.get("firstname")
            request.state.lastname = payload.get("lastname")

        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper

# ========================
# Validar solo admin
# ========================
def validateadmin(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        try:
            schema, token = authorization.split()
            if schema.lower() != "bearer":
                raise HTTPException(status_code=400, detail="Invalid auth schema")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if not payload.get("active") or not payload.get("admin"):
                raise HTTPException(status_code=403, detail="User is not admin")

            request.state.id = payload.get("id")
            request.state.email = payload.get("email")
            request.state.firstname = payload.get("firstname")
            request.state.lastname = payload.get("lastname")
            request.state.admin = payload.get("admin")

        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper

# ========================
# Validar solo cliente
# ========================
def validateclient(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        try:
            schema, token = authorization.split()
            if schema.lower() != "bearer":
                raise HTTPException(status_code=400, detail="Invalid auth schema")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if not payload.get("active") or payload.get("admin") or payload.get("profesional"):
                raise HTTPException(status_code=403, detail="Not a client user")

            request.state.id = payload.get("id")
            request.state.email = payload.get("email")

        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper

# ========================
# Validar solo profesional
# ========================
def validateprofesional(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        try:
            schema, token = authorization.split()
            if schema.lower() != "bearer":
                raise HTTPException(status_code=400, detail="Invalid auth schema")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            if not payload.get("active") or not payload.get("profesional"):
                raise HTTPException(status_code=403, detail="User is not a professional")

            request.state.id = payload.get("id")
            request.state.email = payload.get("email")

        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper

# ========================
# Validar admin o profesional
# ========================
def validateadmin_or_profesional(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request") or args[-1]
        credentials: HTTPAuthorizationCredentials = await security(request)

        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token inválido")

        if not payload.get("admin") and not payload.get("profesional"):
            raise HTTPException(status_code=403, detail="No autorizado")

        # ✅ Aquí seteamos el usuario en request.state.user
        request.state.user = {
            "id": payload["id"],
            "email": payload["email"],
            "admin": payload.get("admin", False),
            "profesional": payload.get("profesional", False)
        }

        return await func(*args, **kwargs)

    return wrapper