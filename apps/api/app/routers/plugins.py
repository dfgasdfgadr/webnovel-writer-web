"""Plugin management API — list, load, and control plugin agents."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import get_current_user
from app.services.plugin_loader import get_plugin_loader

logger = logging.getLogger("novelcraft.plugins")
router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


@router.get("")
async def list_plugins(
    current_user: User = Depends(get_current_user),
):
    """List all discovered plugins and their status."""
    loader = get_plugin_loader()
    return {"plugins": loader.list_plugins(), "total": len(loader.plugins)}


@router.post("/{plugin_name}/load")
async def load_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_user),
):
    """Load a specific plugin by name."""
    loader = get_plugin_loader()
    if plugin_name not in loader.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")

    instance = loader.load_plugin(plugin_name)
    if instance is None:
        raise HTTPException(status_code=500, detail=f"Failed to load plugin: {plugin_name}")

    return {
        "name": plugin_name,
        "loaded": True,
        "type": type(instance).__name__,
    }


@router.post("/{plugin_name}/toggle")
async def toggle_plugin(
    plugin_name: str,
    enabled: bool,
    current_user: User = Depends(get_current_user),
):
    """Enable or disable a plugin."""
    loader = get_plugin_loader()
    if plugin_name not in loader.plugins:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_name}")

    loader.plugins[plugin_name].enabled = enabled
    return {"name": plugin_name, "enabled": enabled}


@router.post("/reload")
async def reload_plugins(
    current_user: User = Depends(get_current_user),
):
    """Re-scan the plugins directory."""
    loader = get_plugin_loader()
    loader.plugins.clear()
    discovered = loader.scan()
    return {"discovered": len(discovered), "plugins": loader.list_plugins()}
