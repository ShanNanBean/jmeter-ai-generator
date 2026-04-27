"""LLM Parser — orchestrates LLM calls to parse natural language into IR JSON."""

import json
import re
import os
from typing import Optional, Tuple

from core.llm_adapter import LLMProviderRegistry, LLMResponse
from core.ir_model import IRDocument


class LLMParser:
    """Orchestrates LLM calls to parse natural language into IR JSON."""

    def __init__(self, registry: LLMProviderRegistry):
        self.registry = registry

    def _build_system_prompt(self) -> str:
        parts = []
        prompt_path = os.path.join("prompts", "system_prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, encoding="utf-8") as f:
                parts.append(f.read())

        catalog_path = os.path.join("prompts", "component_catalog.md")
        if os.path.exists(catalog_path):
            with open(catalog_path, encoding="utf-8") as f:
                parts.append("\n\n## Component Catalog\n" + f.read())

        schema_path = os.path.join("schemas", "ir_schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, encoding="utf-8") as f:
                parts.append("\n\n## IR Schema\n" + f.read())

        return "\n".join(parts)

    def _build_preview_prompt(self) -> str:
        prompt_path = os.path.join("prompts", "preview_prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, encoding="utf-8") as f:
                return f.read()
        return self._build_system_prompt()

    def _build_user_prompt(self, user_input: str, mode: str = "natural") -> str:
        if mode == "natural":
            return f"Parse the following test scenario description into IR JSON:\n\n{user_input}"
        elif mode == "semi_structured":
            return f"Parse the following semi-structured test specification into IR JSON:\n\n{user_input}"
        elif mode == "api_spec":
            return (
                "Generate an IR JSON test plan based on this API specification "
                "and supplementary description:\n\n" + user_input
            )
        return user_input

    def _extract_json(self, raw_content: str) -> str:
        """Extract JSON from LLM response, handling markdown fences."""
        # Try markdown code fence first
        match = re.search(r"```json\s*(.*?)\s*```", raw_content, re.DOTALL)
        if match:
            return match.group(1)
        # Try generic code fence
        match = re.search(r"```\s*(.*?)\s*```", raw_content, re.DOTALL)
        if match:
            candidate = match.group(1)
            if candidate.strip().startswith("{"):
                return candidate
        # Try raw JSON object
        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if match:
            return match.group(0)
        return raw_content

    async def parse_to_ir(
        self,
        user_input: str,
        mode: str = "natural",
        provider_name: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Tuple[IRDocument, LLMResponse]:
        """Parse user input into an IRDocument via LLM."""
        provider = self.registry.get_provider(provider_name)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, mode)

        response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        json_str = self._extract_json(response.content)
        ir_dict = json.loads(json_str)
        ir_doc = IRDocument.model_validate(ir_dict)

        return ir_doc, response

    async def update_ir_with_feedback(
        self,
        ir: IRDocument,
        feedback: str,
        provider_name: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Tuple[IRDocument, LLMResponse]:
        """Modify IR based on user feedback via LLM."""
        provider = self.registry.get_provider(provider_name)
        system_prompt = self._build_system_prompt()

        ir_json = json.dumps(ir.model_dump(), indent=2, ensure_ascii=False)
        user_prompt = (
            f"Current IR JSON:\n```\n{ir_json}\n```\n\n"
            f"User feedback for modification:\n{feedback}\n\n"
            "Please output the modified IR JSON. Only output the JSON, nothing else."
        )

        response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        json_str = self._extract_json(response.content)
        ir_dict = json.loads(json_str)
        ir_doc = IRDocument.model_validate(ir_dict)

        return ir_doc, response