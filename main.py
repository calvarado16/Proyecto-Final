import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv

# Controladores y modelos
from controllers.users import create_user, login
from models.users import User
from models.login import Login

# Seguridad
from utils.security import create_jwt_token, validateuser, validateadmin

# Routers
from routes.service_offering import router as service_offering_router
from routes.reservation import router as reservation_router
from routes.profession import router as profession_router
from routes.review import router as review_router
from routes.service_review import router as service_review_router
from routes.public_profession import router as public_profession_router

# MongoDB
from utils.mongodb import t_connection

# Swagger
from fastapi.openapi.utils import get_openapi

# CORS
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# ============================
# CORS
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Routers
# ============================
app.include_router(reservation_router)
app.include_router(profession_router)
app.include_router(service_offering_router)
app.include_router(review_router)
app.include_router(service_review_router)
app.include_router(public_profession_router)

# ============================
# Personalización OpenAPI
# ============================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="FastAPI",
        version="0.1.0",
        description="API con autenticación JWT",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================
# Logger
# ============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# Endpoints principales
# ============================
@app.get("/")
def read_root():
    return {"status": "healthy", "version": "0.0.0", "service": "servicios-api"}

@app.get("/health")
def health_check():
    try:
        return {
            "status": "healthy",
            "timestamp": "2025-08-11",
            "service": "servicios-api",
            "environment": "production"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/ready")
def readiness_check():
    try:
        db_status = t_connection()
        return {
            "status": "ready" if db_status else "not ready",
            "database": "connected" if db_status else "disconnected",
            "service": "servicios-api",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# ============================
# Endpoints de usuarios
# ============================
@app.post("/users")
async def create_user_endpoint(user: User) -> User:
    try:
        return await create_user(user)
    except Exception as e:
        logger.error("Error al crear usuario", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login_access(l: Login):
    return await login(l)


    return {"email": email, "found": bool(u), "doc": _serialize_user(u)}


# ============================
# Arranque
# ============================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


