from fastapi import APIRouter
from app.api.v1.worldview import router as worldview_router
from app.api.v1.character import router as character_router
from app.api.v1.capsule import router as capsule_router
from app.api.v1.avg import router as avg_router
from app.api.v1.hall import router as hall_router

api_v1_router = APIRouter()
api_v1_router.include_router(worldview_router)
api_v1_router.include_router(character_router)
api_v1_router.include_router(capsule_router)
api_v1_router.include_router(avg_router)
api_v1_router.include_router(hall_router)
