"""Config API routes."""

from fastapi import APIRouter
from api.models.request_models import ProviderInfo
from core.llm_adapter import LLMProviderRegistry
from components.registry import TemplateRegistry
import yaml
import os

router = APIRouter()


@router.get("/providers")
async def list_providers():
    """List available LLM providers."""
    registry = LLMProviderRegistry()
    providers = []
    config_path = "config/llm_providers.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    for name, prov in config.get("providers", {}).items():
        providers.append(ProviderInfo(
            name=name,
            model=prov.get("model", ""),
            type=prov.get("type", name),
        ))
    return providers


@router.get("/components")
async def list_components():
    """List available component templates."""
    registry = TemplateRegistry()
    return registry.list_available_types()


@router.get("/status")
async def get_status():
    """Health check and config info."""
    registry = LLMProviderRegistry()
    return {
        "status": "ok",
        "version": "0.1.0",
        "providers": registry.list_providers(),
        "components_count": len(TemplateRegistry().list_available_types()),
    }