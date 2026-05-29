from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.chapters import router as chapters_router
from app.routers.health import router as health_router
from app.routers.agents import router as agents_router
from app.routers.cards import router as cards_router
from app.routers.settings import router as settings_router
from app.routers.simulations import router as simulations_router
from app.routers.disambiguation import router as disambiguation_router
from app.routers.summaries import router as summaries_router
from app.routers.plugins import router as plugins_router
from app.routers.reference_corpora import router as reference_corpora_router
from app.routers.deconstruct_runs import router as deconstruct_runs_router

__all__ = ["auth_router", "projects_router", "chapters_router", "health_router", "agents_router", "cards_router", "settings_router", "simulations_router", "disambiguation_router", "summaries_router", "plugins_router", "reference_corpora_router", "deconstruct_runs_router"]
