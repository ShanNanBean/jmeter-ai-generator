"""Dependency Checker — validates variable definition-reference chains."""

import re
from typing import List, Set

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