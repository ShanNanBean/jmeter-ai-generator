"""Validation API routes."""

from fastapi import APIRouter
from api.models.request_models import ValidateJMXRequest, ValidateIRRequest, ValidationResponse
from core.validator import JMXValidator
from core.ir_model import IRDocument
from core.reasonableness_checker import ReasonablenessChecker

router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_jmx(request: ValidateJMXRequest):
    """Validate a JMX XML string."""
    validator = JMXValidator()
    result = validator.validate(request.jmx)
    return ValidationResponse(
        valid=result.valid,
        issues=[
            {
                "severity": i.severity,
                "category": i.category,
                "message": i.message,
                "location": i.location,
            }
            for i in result.issues
        ],
    )


@router.post("/validate-ir", response_model=ValidationResponse)
async def validate_ir(request: ValidateIRRequest):
    """Validate IR structure."""
    try:
        IRDocument.model_validate(request.ir)
        return ValidationResponse(valid=True, issues=[])
    except Exception as e:
        return ValidationResponse(
            valid=False,
            issues=[{"severity": "error", "category": "structure", "message": str(e)}],
        )


@router.post("/validate-ir-reasonable", response_model=ValidationResponse)
async def validate_ir_reasonable(request: ValidateIRRequest):
    """Check whether IR settings look reasonable for load testing goals."""
    try:
        ir_doc = IRDocument.model_validate(request.ir)
    except Exception as e:
        return ValidationResponse(
            valid=False,
            issues=[{"severity": "error", "category": "structure", "message": str(e)}],
        )

    issues = ReasonablenessChecker().validate(ir_doc)
    return ValidationResponse(valid=not any(i["severity"] == "error" for i in issues), issues=issues)
