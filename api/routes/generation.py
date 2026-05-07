"""Generation API routes."""

from fastapi import APIRouter, HTTPException
from api.models.request_models import (
    ParseRequest, ParseResponse, GenerateRequest, GenerateResponse,
    QPSDeriveRequest, QPSDeriveResponse,
)
from core.llm_adapter import LLMProviderRegistry
from core.llm_parser import LLMParser
from core.ir_model import IRDocument
from core.assembler import JMXAssembler
from core.validator import JMXValidator
from core.qps_deriver import QPSDeriver
from core.plugin_analyzer import PluginAnalyzer

router = APIRouter()

# Module-level singletons (initialized once)
_registry = None
_parser = None
_assembler = None


def _init_modules():
    global _registry, _parser, _assembler
    if _registry is None:
        _registry = LLMProviderRegistry()
        _parser = LLMParser(_registry)
        _assembler = JMXAssembler()


@router.post("/parse", response_model=ParseResponse)
async def parse_input(request: ParseRequest):
    """Parse natural language input into IR JSON via LLM."""
    _init_modules()
    try:
        ir_doc, llm_response = await _parser.parse_to_ir(
            user_input=request.user_input,
            mode=request.mode,
            provider_name=request.provider,
            temperature=request.temperature,
        )
        return ParseResponse(
            ir=ir_doc.model_dump(),
            llm_usage=llm_response.usage,
            raw_llm_response=llm_response.content,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateResponse)
async def generate_jmx(request: GenerateRequest):
    """Generate JMX from IR JSON."""
    _init_modules()
    try:
        ir_doc = IRDocument.model_validate(request.ir)
        assembler = JMXAssembler(jmeter_version=request.jmeter_version)
        jmx_str = assembler.assemble(ir_doc)

        validation_result = None
        if request.run_validation:
            validator = JMXValidator()
            result = validator.validate(jmx_str)
            validation_result = {
                "valid": result.valid,
                "issues": [
                    {
                        "severity": i.severity,
                        "category": i.category,
                        "message": i.message,
                        "location": i.location,
                    }
                    for i in result.issues
                ],
            }

        plugin_info = PluginAnalyzer().analyze(ir_doc)

        filename = f"{ir_doc.testPlan.name.replace(' ', '_')}.jmx"
        return GenerateResponse(
            jmx=jmx_str,
            validation=validation_result,
            filename=filename,
            plugin_info=plugin_info,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/derive-qps", response_model=QPSDeriveResponse)
async def derive_qps(request: QPSDeriveRequest):
    """Derive thread group parameters from target QPS."""
    try:
        deriver = QPSDeriver()
        return deriver.derive(
            target_qps=request.target_qps,
            scenario_steps=request.scenario_steps,
            think_time_range=request.think_time_range,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_generation(request: ParseRequest):
    """Stream LLM generation (SSE endpoint)."""
    _init_modules()
    from fastapi.responses import StreamingResponse

    provider = _registry.get_provider(request.provider)

    system_prompt = _parser.build_system_prompt()
    user_prompt = _parser.build_user_prompt(request.user_input, request.mode)

    async def event_stream():
        async for chunk in provider.stream(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=request.temperature,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")