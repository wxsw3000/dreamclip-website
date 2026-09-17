from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.microservice import router as microservice_router
from app.api.v1.user import router as user_router
from app.api.v1.dict_config import router as dict_config_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(microservice_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(dict_config_router)
