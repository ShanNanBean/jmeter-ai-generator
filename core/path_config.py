"""Shared filesystem paths for project resources."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
COMPONENTS_DIR = PROJECT_ROOT / "components"
EXTENSIONS_DIR = PROJECT_ROOT / "extensions"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
