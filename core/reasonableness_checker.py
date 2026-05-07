"""Validation-style reasonableness checks for IR documents."""

from core.ir_model import IRDocument
from core.sanity_checker import SanityChecker


class ReasonablenessChecker:
    """Wraps sanity warnings as validation issues."""

    def validate(self, ir: IRDocument):
        issues = []
        for warning in SanityChecker().check(ir):
            issues.append({
                "severity": warning.get("severity", "warning"),
                "category": warning.get("category", "reasonableness"),
                "message": warning.get("message", ""),
                "location": warning.get("location"),
            })
        return issues
