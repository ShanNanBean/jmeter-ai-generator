"""Business-level sanity checks for generated load-test scenarios."""

from typing import Any, Dict, List, Optional

from core.dependency_checker import DependencyChecker
from core.ir_model import IRDocument


class SanityChecker:
    """Produces non-blocking warnings about whether a plan looks reasonable."""

    def check(self, ir: IRDocument) -> List[Dict[str, Any]]:
        warnings: List[Dict[str, Any]] = []
        warnings.extend(self._thread_group_warnings(ir))
        warnings.extend(self._assertion_warnings(ir))
        warnings.extend(self._think_time_warnings(ir))
        warnings.extend(self._dependency_warnings(ir))
        return warnings

    def _thread_group_warnings(self, ir: IRDocument) -> List[Dict[str, Any]]:
        warnings = []
        for tg in ir.threadGroups:
            if tg.threads >= 200 and tg.rampUp <= 10:
                warnings.append(self._warning(
                    category="load_model",
                    message=f"线程组“{tg.name}”会在 {tg.rampUp} 秒内启动 {tg.threads} 个虚拟用户，启动过快可能造成瞬时尖峰。",
                    suggestion="建议拉长 Ramp-up，或拆成多个阶段逐步升压。",
                    location=tg.name,
                ))
            if tg.duration is not None and tg.duration < 60:
                warnings.append(self._warning(
                    category="load_model",
                    severity="info",
                    message=f"线程组“{tg.name}”持续时间只有 {tg.duration} 秒，更适合冒烟验证，不适合观察稳定压测结果。",
                    suggestion="正式压测通常需要更长持续时间以观察吞吐、错误率和响应时间趋势。",
                    location=tg.name,
                ))
            if (tg.loop or 0) > 1000 and not tg.duration:
                warnings.append(self._warning(
                    category="load_model",
                    message=f"线程组“{tg.name}”设置了较大的循环次数，但没有持续时间上限。",
                    suggestion="建议设置持续时间，避免脚本运行时间不可控。",
                    location=tg.name,
                ))
        return warnings

    def _assertion_warnings(self, ir: IRDocument) -> List[Dict[str, Any]]:
        warnings = []
        for scenario in ir.scenarios:
            steps_without_assertions = [step.name for step in scenario.steps if not step.assertions]
            if steps_without_assertions:
                warnings.append(self._warning(
                    category="validation",
                    severity="info",
                    message=f"场景“{scenario.name}”中有 {len(steps_without_assertions)} 个接口没有校验规则。",
                    suggestion="建议至少校验状态码、关键字段或响应时间，避免接口失败但压测报告仍显示成功。",
                    location=scenario.name,
                ))
        return warnings

    def _think_time_warnings(self, ir: IRDocument) -> List[Dict[str, Any]]:
        warnings = []
        for scenario in ir.scenarios:
            step_count = len(scenario.steps or [])
            has_scenario_timer = bool(scenario.timers)
            has_step_timer = any(step.timers for step in scenario.steps)
            if step_count > 1 and not has_scenario_timer and not has_step_timer:
                warnings.append(self._warning(
                    category="pacing",
                    severity="info",
                    message=f"场景“{scenario.name}”包含多个连续接口，但没有等待时间。",
                    suggestion="如果要模拟真实用户行为，建议在关键步骤间加入思考时间；如果要压接口极限，可以保持无等待。",
                    location=scenario.name,
                ))
        return warnings

    def _dependency_warnings(self, ir: IRDocument) -> List[Dict[str, Any]]:
        dep_issues = DependencyChecker().check(ir)
        return [
            self._warning(
                category="variable_dependency",
                message=issue,
                suggestion="请确认登录 token、订单号等动态参数已经在前置接口中提取，再在后续接口中引用。",
            )
            for issue in dep_issues
        ]

    def _warning(
        self,
        category: str,
        message: str,
        suggestion: Optional[str] = None,
        location: Optional[str] = None,
        severity: str = "warning",
    ) -> Dict[str, Any]:
        return {
            "severity": severity,
            "category": category,
            "message": message,
            "suggestion": suggestion,
            "location": location,
        }
