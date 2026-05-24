from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.chapters import router as chapters_router
from app.routers.health import router as health_router
from app.routers.agents import router as agents_router

__all__ = ["auth_router", "projects_router", "chapters_router", "health_router", "agents_router"]
