"""Dependency Checker — validates variable definition-reference chains."""

import re
from typing import Any, Dict, List, Set

from core.ir_model import IRDocument


JMETER_BUILTIN_FUNCTIONS = {
    "__Random", "__threadNum", "__time", "__counter", "__V",
    "__property", "__P", "__UUID", "__machineName", "__ip",
    "__Split", "__RegexFunction", "__encodeURIComponent",
}


class DependencyChecker:
    """Validates variable definition-reference chains across steps."""

    def check(self, ir: IRDocument) -> List[str]:
        issues = []

        # Collect test plan variables
        defined_vars: Set[str] = set()
        if ir.testPlan.variables:
            for var in ir.testPlan.variables:
                defined_vars.add(var.key)

        # Walk scenarios step-by-step
        for scenario in ir.scenarios:
            # Data source variables (available from start)
            for ds in (scenario.dataSources or []):
                if ds.vars:
                    defined_vars.update(ds.vars)
                if ds.variable:
                    defined_vars.add(ds.variable)

            # Walk steps in order
            available = set(defined_vars)
            for step in scenario.steps:
                # Check references in this step
                refs = self._extract_references(step)
                for ref in refs:
                    if ref in JMETER_BUILTIN_FUNCTIONS:
                        continue
                    if ref not in available:
                        issues.append(
                            f"Step '{step.name}' references ${{{ref}}}, "
                            f"but it is not defined before this step"
                        )

                # Add variables produced by extractors of this step
                for ext in (step.extractors or []):
                    available.add(ext.variable)

        return issues

    def get_variable_chains(self, ir: IRDocument) -> List[Dict[str, Any]]:
        """Build variable source and usage chains for preview display."""
        chains: Dict[str, Dict[str, Any]] = {}

        if ir.testPlan.variables:
            for var in ir.testPlan.variables:
                chains[var.key] = {
                    "variable": var.key,
                    "source": "测试计划变量",
                    "source_step": None,
                    "usages": [],
                }

        for scenario in ir.scenarios:
            for ds in scenario.dataSources or []:
                for var_name in ds.vars or []:
                    chains.setdefault(var_name, {
                        "variable": var_name,
                        "source": f"数据源 {ds.file or ds.type.value}",
                        "source_step": None,
                        "usages": [],
                    })
                if ds.variable:
                    chains.setdefault(ds.variable, {
                        "variable": ds.variable,
                        "source": f"数据源 {ds.type.value}",
                        "source_step": None,
                        "usages": [],
                    })

            for step in scenario.steps:
                for ref in self._extract_references(step):
                    if ref in JMETER_BUILTIN_FUNCTIONS:
                        continue
                    chains.setdefault(ref, {
                        "variable": ref,
                        "source": "未找到来源",
                        "source_step": None,
                        "usages": [],
                    })
                    chains[ref]["usages"].append({
                        "scenario": scenario.name,
                        "step": step.name,
                        "field": "请求参数/路径/请求头/Body",
                    })

                for ext in step.extractors or []:
                    chains[ext.variable] = {
                        "variable": ext.variable,
                        "source": f"接口响应提取（{ext.type.value}）",
                        "source_step": step.name,
                        "usages": chains.get(ext.variable, {}).get("usages", []),
                    }

        return list(chains.values())

    def _extract_references(self, step) -> Set[str]:
        """Find all ${variable} references in a step's fields."""
        refs = set()
        pattern = re.compile(r"\$\{([^}]+)\}")

        fields_to_check = []
        if step.body:
            fields_to_check.append(step.body)
        if step.path:
            fields_to_check.append(step.path)
        if step.params:
            for p in step.params:
                fields_to_check.append(p.get("value", ""))
        if step.headers:
            for h in step.headers:
                fields_to_check.append(h.get("value", ""))

        for field in fields_to_check:
            if field:
                for match in pattern.findall(field):
                    # Strip nested function calls like ${__Random(1,10)}
                    if match.startswith("__"):
                        continue
                    refs.add(match)

        return refs