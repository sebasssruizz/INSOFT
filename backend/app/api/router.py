from fastapi import APIRouter

from app.api.routes import auth, ai, content, courses, progress, rag, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(content.router)
api_router.include_router(progress.router)
api_router.include_router(rag.router)
api_router.include_router(ai.router)
