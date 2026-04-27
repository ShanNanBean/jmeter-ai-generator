"""API request/response models."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# Generation
class ParseRequest(BaseModel):
    user_input: str
    mode: str = "natural"  # natural, semi_structured, api_spec
    provider: Optional[str] = None
    temperature: float = 0.3


class ParseResponse(BaseModel):
    ir: Dict[str, Any]
    llm_usage: Dict[str, int]
    raw_llm_response: Optional[str] = None


class GenerateRequest(BaseModel):
    ir: Dict[str, Any]
    run_validation: bool = True
    jmeter_version: Optional[str] = "5.0"


class GenerateResponse(BaseModel):
    jmx: str
    validation: Optional[Dict[str, Any]] = None
    filename: str


# Preview
class PreviewRequest(BaseModel):
    ir: Dict[str, Any]
    user_input: Optional[str] = None


class PreviewResponse(BaseModel):
    preview_text: str
    dependency_issues: List[str]
    thread_params: Optional[Dict[str, Any]] = None
    ir: Optional[Dict[str, Any]] = None


class UpdatePreviewRequest(BaseModel):
    ir: Dict[str, Any]
    feedback: str
    provider: Optional[str] = None
    temperature: float = 0.3


class DependencyCheckRequest(BaseModel):
    ir: Dict[str, Any]


class DependencyCheckResponse(BaseModel):
    issues: List[str]


# Validation
class ValidateJMXRequest(BaseModel):
    jmx: str


class ValidateIRRequest(BaseModel):
    ir: Dict[str, Any]


class ValidationResponse(BaseModel):
    valid: bool
    issues: List[Dict[str, Any]]


# Config
class ProviderInfo(BaseModel):
    name: str
    model: str
    type: str