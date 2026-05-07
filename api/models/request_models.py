"""API request/response models."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# Generation
class ParseRequest(BaseModel):
    user_input: str
    mode: str = "natural"  # natural, semi_structured, api_spec
    provider: Optional[str] = None
    temperature: float = 0.3
    pressure_goal: Optional[Dict[str, Any]] = None
    allowed_plugins: Optional[List[str]] = None
    parse_preference: Optional[str] = None


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
    plugin_info: List[Dict[str, Any]] = []


class PlanSummary(BaseModel):
    test_plan_name: str
    thread_group_count: int
    scenario_count: int
    step_count: int
    total_threads: int
    duration_seconds: Optional[int] = None
    thread_groups: List[Dict[str, Any]] = []
    variable_chains: List[Dict[str, Any]] = []


class SanityWarning(BaseModel):
    severity: str = "warning"
    category: str
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None


class VariableChain(BaseModel):
    variable: str
    source: str
    source_step: Optional[str] = None
    usages: List[Dict[str, str]] = []


class PluginInfo(BaseModel):
    name: str
    required: bool = False
    description: str
    component: Optional[str] = None
    severity: str = "info"


class QPSDeriveRequest(BaseModel):
    target_qps: int
    scenario_steps: Optional[List[Dict[str, Any]]] = None
    think_time_range: Optional[List[int]] = None


class QPSDeriveResponse(BaseModel):
    threads: int
    rampUp: int
    duration: int
    loop: int
    qpsNote: str


# Preview
class PreviewRequest(BaseModel):
    ir: Dict[str, Any]
    user_input: Optional[str] = None


class PreviewResponse(BaseModel):
    preview_text: str
    dependency_issues: List[str]
    thread_params: Optional[Dict[str, Any]] = None
    ir: Optional[Dict[str, Any]] = None
    plan_summary: Optional[PlanSummary] = None
    sanity_warnings: List[SanityWarning] = []
    variable_chains: List[VariableChain] = []


class UpdatePreviewRequest(BaseModel):
    ir: Dict[str, Any]
    feedback: str
    provider: Optional[str] = None
    temperature: float = 0.3


class DependencyCheckRequest(BaseModel):
    ir: Dict[str, Any]


class DependencyCheckResponse(BaseModel):
    issues: List[str]
    variable_chains: List[VariableChain] = []


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