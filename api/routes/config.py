"""Config API routes."""

from fastapi import APIRouter
import yaml

from api.models.request_models import ProviderInfo
from components.registry import TemplateRegistry
from core.path_config import CONFIG_DIR

router = APIRouter()

_llm_config = None
_template_registry = None
_version_config = None


def _load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_llm_config():
    global _llm_config
    if _llm_config is None:
        _llm_config = _load_yaml(CONFIG_DIR / "llm_providers.yaml")
    return _llm_config


def _get_template_registry():
    global _template_registry
    if _template_registry is None:
        _template_registry = TemplateRegistry()
    return _template_registry


def _get_version_config():
    global _version_config
    if _version_config is None:
        _version_config = _load_yaml(CONFIG_DIR / "jmeter_versions.yaml")
    return _version_config


@router.get("/providers")
async def list_providers():
    """List available LLM providers."""
    providers = []
    for name, prov in _get_llm_config().get("providers", {}).items():
        providers.append(ProviderInfo(
            name=name,
            model=prov.get("model", ""),
            type=prov.get("type", name),
        ))
    return providers


@router.get("/components")
async def list_components():
    """List available component templates."""
    return _get_template_registry().list_available_types()


@router.get("/jmeter-versions")
async def list_jmeter_versions():
    """List supported JMeter versions."""
    config = _get_version_config()
    versions = list(config.get("versions", {}).keys())
    return {"default": config.get("default", "5.0"), "available": versions}


@router.get("/status")
async def get_status():
    """Health check and config info."""
    providers = [provider.name for provider in await list_providers()]
    versions = await list_jmeter_versions()
    return {
        "status": "ok",
        "version": "0.1.0",
        "providers": providers,
        "components_count": len(_get_template_registry().list_available_types()),
        "jmeter_versions": versions["available"],
    }
