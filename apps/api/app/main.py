from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.db.schema import sync_sqlite_schema
from app.routers import auth_router, projects_router, chapters_router, health_router, agents_router, cards_router, settings_router, simulations_router, disambiguation_router, summaries_router, plugins_router, reference_corpora_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # SQLite DDL inside engine.begin() can deadlock with aiosqlite on Windows.
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(sync_sqlite_schema)
        await conn.commit()
    # Initialize plugin loader at startup
    from app.services.plugin_loader import get_plugin_loader
    get_plugin_loader(settings.plugins_dir)
    yield


app = FastAPI(
    title="NovelCraft API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(chapters_router)
app.include_router(agents_router)
app.include_router(cards_router)
app.include_router(settings_router)
app.include_router(simulations_router)
app.include_router(disambiguation_router)
app.include_router(summaries_router)
app.include_router(plugins_router)
app.include_router(reference_corpora_router)
