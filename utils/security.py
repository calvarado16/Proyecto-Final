import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from functools import wraps
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")  # asegúrate que exista

# -------------------------
# Crear JWT
# -------------------------
def create_jwt_token(
    *,
    id: str,
    firstname: str,
    lastname: str,
    email: str,
    active: bool,
    admin: bool,
) -> str:
    """Genera un JWT HS256 con exp de 1 hora."""
    now = datetime.utcnow()
    payload = {
        "id": id,
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "active": active,
        "admin": admin,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY no configurado")
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# -------------------------
# Helpers internos
# -------------------------
def _get_request_from_args_kwargs(*args, **kwargs) -> Request:
    req = kwargs.get("request")
    if req is None:
        for a in args:
            if isinstance(a, Request):
                req = a
                break
    if req is None:
        raise HTTPException(status_code=400, detail="Request object not found")
    return req

def _extract_bearer_token(req: Request) -> str:
    auth = req.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        scheme, token = auth.split()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Authorization header")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=400, detail="Invalid auth schema")
    return token

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def _attach_user_to_request(req: Request, payload: dict) -> None:
    # 🔹 Compatibilidad con controladores que esperan request.state.user
    req.state.user = payload

    # 🔹 Campos individuales
    req.state.id = payload.get("id")
    req.state.user_id = payload.get("id")
    req.state.email = payload.get("email")
    req.state.firstname = payload.get("firstname")
    req.state.lastname = payload.get("lastname")
    req.state.admin = bool(payload.get("admin", False))
    req.state.active = bool(payload.get("active", False))

# -------------------------
# Decoradores públicos
# -------------------------
def validateuser(func):
    """Requiere: token válido + usuario activo."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        req = _get_request_from_args_kwargs(*args, **kwargs)
        token = _extract_bearer_token(req)
        payload = _decode_token(token)

        if not payload.get("active"):
            raise HTTPException(status_code=401, detail="Inactive user")

        _attach_user_to_request(req, payload)
        return await func(*args, **kwargs)
    return wrapper

def validateadmin(func):
    """Requiere: token válido + usuario activo + admin=True."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        req = _get_request_from_args_kwargs(*args, **kwargs)
        token = _extract_bearer_token(req)
        payload = _decode_token(token)

        if not payload.get("active"):
            raise HTTPException(status_code=401, detail="Inactive user")
        if not payload.get("admin"):
            raise HTTPException(status_code=403, detail="User is not admin")

        _attach_user_to_request(req, payload)
        return await func(*args, **kwargs)
    return wrapper


