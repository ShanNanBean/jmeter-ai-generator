"""Preview API routes."""

from fastapi import APIRouter, HTTPException
from api.models.request_models import (
    PreviewRequest, PreviewResponse,
    UpdatePreviewRequest, DependencyCheckRequest, DependencyCheckResponse,
)
from core.llm_adapter import LLMProviderRegistry
from core.llm_parser import LLMParser
from core.ir_model import IRDocument
from core.scenario_preview import ScenarioPreviewGenerator
from core.dependency_checker import DependencyChecker

router = APIRouter()

_registry = None
_parser = None
_preview_gen = None


def _init_modules():
    global _registry, _parser, _preview_gen
    if _registry is None:
        _registry = LLMProviderRegistry()
        _parser = LLMParser(_registry)
        _preview_gen = ScenarioPreviewGenerator()


@router.post("/generate", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """Generate scenario preview from IR."""
    _init_modules()
    try:
        ir_doc = IRDocument.model_validate(request.ir)
        preview_text = _preview_gen.generate(ir_doc)

        dep_checker = DependencyChecker()
        dep_issues = dep_checker.check(ir_doc)

        return PreviewResponse(
            preview_text=preview_text,
            dependency_issues=dep_issues,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=PreviewResponse)
async def update_preview(request: UpdatePreviewRequest):
    """Update IR based on user feedback and regenerate preview."""
    _init_modules()
    try:
        ir_doc = IRDocument.model_validate(request.ir)
        new_ir, llm_response = await _parser.update_ir_with_feedback(
            ir=ir_doc,
            feedback=request.feedback,
            provider_name=request.provider,
            temperature=request.temperature,
        )

        new_ir_dict = new_ir.model_dump()

        preview_text = _preview_gen.generate(new_ir)
        dep_checker = DependencyChecker()
        dep_issues = dep_checker.check(new_ir)

        return PreviewResponse(
            preview_text=preview_text,
            dependency_issues=dep_issues,
            ir=new_ir_dict,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependency-check", response_model=DependencyCheckResponse)
async def dependency_check(request: DependencyCheckRequest):
    """Check variable dependencies for given IR."""
    try:
        ir_doc = IRDocument.model_validate(request.ir)
        dep_checker = DependencyChecker()
        issues = dep_checker.check(ir_doc)
        return DependencyCheckResponse(issues=issues)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))