"""Scenario Preview Generator — generates human-readable pseudo-script from IR."""

from typing import Any, Dict, List

from core.ir_model import IRDocument, StepModel
from core.dependency_checker import DependencyChecker


class ScenarioPreviewGenerator:
    """Generates human-readable pseudo-script from IR for user confirmation."""

    def __init__(self):
        self.dep_checker = DependencyChecker()

    def generate(self, ir: IRDocument) -> str:
        sections = []

        # Section 1: Header
        sections.append(self._header(ir))

        # Section 2: Business explanation
        sections.append(self._design_explanation(ir))

        # Section 3: Thread group params
        sections.append(self._thread_params(ir))

        # Section 4: Business flow
        sections.append(self._flow(ir))

        # Section 5: Data sources
        sections.append(self._data_sources(ir))

        # Section 6: Global config
        sections.append(self._global_config(ir))

        # Section 7: Result collection
        sections.append(self._listeners(ir))

        # Section 8: Variable dependency check
        dep_issues = self.dep_checker.check(ir)
        sections.append(self._dependency_report(dep_issues))

        return "\n\n".join(sections)

    def build_plan_summary(self, ir: IRDocument) -> Dict[str, Any]:
        """Build structured summary used by the beginner-oriented preview UI."""
        step_count = sum(len(scenario.steps or []) for scenario in ir.scenarios)
        total_threads = sum(tg.threads for tg in ir.threadGroups)
        durations = [tg.duration for tg in ir.threadGroups if tg.duration]
        return {
            "test_plan_name": ir.testPlan.name,
            "thread_group_count": len(ir.threadGroups),
            "scenario_count": len(ir.scenarios),
            "step_count": step_count,
            "total_threads": total_threads,
            "duration_seconds": max(durations) if durations else None,
            "thread_groups": [
                {
                    "name": tg.name,
                    "threads": tg.threads,
                    "rampUp": tg.rampUp,
                    "duration": tg.duration,
                    "loop": tg.loop,
                    "scenario_count": sum(1 for scenario in ir.scenarios if scenario.threadGroup == tg.name),
                }
                for tg in ir.threadGroups
            ],
            "variable_chains": self.dep_checker.get_variable_chains(ir),
        }

    def _header(self, ir: IRDocument) -> str:
        name = ir.testPlan.name
        return f"压测场景预览 — {name}\n{'=' * 50}"

    def _design_explanation(self, ir: IRDocument) -> str:
        lines = ["【为什么这样设计】"]
        if ir.threadGroups:
            total_threads = sum(tg.threads for tg in ir.threadGroups)
            lines.append(f"  使用 {len(ir.threadGroups)} 个并发模型，共 {total_threads} 个虚拟用户，用来模拟业务访问压力。")
            for tg in ir.threadGroups:
                lines.append(f"  “{tg.name}”在 {tg.rampUp} 秒内逐步启动，避免所有用户同时涌入造成不真实尖峰。")
                if tg.duration:
                    lines.append(f"  持续运行 {tg.duration} 秒，用于观察吞吐、错误率和响应时间是否稳定。")
                if tg.loop and tg.loop != -1:
                    lines.append(f"  每个虚拟用户重复执行 {tg.loop} 轮业务流程。")
        step_count = sum(len(scenario.steps or []) for scenario in ir.scenarios)
        lines.append(f"  脚本包含 {len(ir.scenarios)} 条业务链路、{step_count} 个接口步骤，按接口依赖顺序执行。")
        chains = self.dep_checker.get_variable_chains(ir)
        if chains:
            lines.append("  已识别动态参数传递链，例如登录 token、订单号等会从前置响应提取后给后续接口使用。")
        has_timer = any(s.timers for s in ir.scenarios) or any(step.timers for s in ir.scenarios for step in s.steps)
        lines.append("  已加入等待时间来模拟真实用户操作节奏。" if has_timer else "  当前未加入等待时间，更偏向接口极限压测；如需模拟真实用户，可在编辑页补充思考时间。")
        return "\n".join(lines)

    def _thread_params(self, ir: IRDocument) -> str:
        lines = ["【压测参数设计】"]
        for tg in ir.threadGroups:
            lines.append(f"  线程数: {tg.threads}")
            lines.append(f"  Ramp-up: {tg.rampUp}s")
            if tg.duration:
                lines.append(f"  持续时间: {tg.duration}s")
            if tg.loop == -1:
                lines.append("  循环模式: 无限循环 (由持续时间控制)")
            else:
                lines.append(f"  循环次数: {tg.loop}")
        return "\n".join(lines)

    def _flow(self, ir: IRDocument) -> str:
        lines = ["【业务流程】"]
        step_num = 1
        for scenario in ir.scenarios:
            if scenario.controllers:
                for ctrl in scenario.controllers:
                    lines.append(f"  Controller: {ctrl.type.value} — {ctrl.name}")

            for step in scenario.steps:
                lines.append(f"  Step {step_num} — {step.name}")
                method = step.method or "GET"
                path = step.path or ""
                lines.append(f"    {method} {path}")

                if step.body:
                    lines.append(f"    Body: {step.body}")

                for ext in (step.extractors or []):
                    ext_detail = ext.path or ext.regex or ext.expression or ""
                    lines.append(f"    提取: {ext.variable} <-- {ext.type.value} {ext_detail}")

                for assertion in (step.assertions or []):
                    detail = assertion.pattern or str(assertion.maxMs or "")
                    lines.append(f"    断言: {assertion.type.value} {detail}")

                if step.headers:
                    for h in step.headers:
                        lines.append(f"    Header: {h['key']}: {h['value']}")

                # Step-level timers
                for timer in (step.timers or []):
                    lines.append(f"    思考时间: {self._timer_desc(timer)}")

                # Step-level config elements
                for pre in (step.preProcessors or []):
                    lines.append(f"    前置处理: {pre.type.value} ({pre.language})")
                for post in (step.postProcessors or []):
                    lines.append(f"    后置处理: {post.type.value} ({post.language})")

                step_num += 1
        return "\n".join(lines)

    def _timer_desc(self, timer) -> str:
        """Describe a timer in human-readable form."""
        if timer.type.value == "ConstantTimer":
            return f"固定 {timer.delayMs}ms"
        elif timer.type.value == "UniformRandomTimer":
            if timer.rangeMs and len(timer.rangeMs) == 2:
                return f"随机 {timer.rangeMs[0]}~{timer.rangeMs[1]}ms"
            return "随机等待"
        elif timer.type.value == "GaussianRandomTimer":
            return f"正态分布 均值{timer.meanMs}ms 偏差{timer.deviationMs}ms"
        return timer.type.value

    def _data_sources(self, ir: IRDocument) -> str:
        lines = ["【数据源】"]
        found = False
        for scenario in ir.scenarios:
            for ds in (scenario.dataSources or []):
                found = True
                if ds.type.value == "CSVDataSet":
                    vars_str = ",".join(ds.vars or [])
                    lines.append(f"  CSV: {ds.file} (字段: {vars_str})")
                elif ds.type.value == "CounterConfig":
                    end_str = str(ds.end) if ds.end else "∞"
                    lines.append(f"  计数器: {ds.variable} ({ds.start}→{end_str})")
                elif ds.type.value == "UserParameters":
                    lines.append(f"  用户参数: {ds.variable}")
        if not found:
            lines.append("  无")
        return "\n".join(lines)

    def _global_config(self, ir: IRDocument) -> str:
        """Generate global config section based on actual IR content."""
        lines = ["【全局配置】"]
        found = False

        # TestPlan-level config elements
        for ce in (ir.configElements or []):
            found = True
            if ce.type.value == "HeaderManager":
                headers = ce.headers or []
                if headers:
                    hdr_str = ", ".join(f"{h['key']}: {h['value']}" for h in headers)
                    lines.append(f"  全局请求头: {hdr_str}")
                else:
                    lines.append("  全局请求头管理器")
            elif ce.type.value == "CookieManager":
                lines.append(f"  Cookie管理: 开启 (每次迭代清空: {ce.clearEachIteration})")
            elif ce.type.value == "CacheManager":
                lines.append(f"  缓存管理: 开启 (使用Expires头: {ce.useExpires})")

        # Scenario-level config elements and timers
        for scenario in ir.scenarios:
            for ce in (scenario.configElements or []):
                found = True
                if ce.type.value == "HeaderManager":
                    headers = ce.headers or []
                    if headers:
                        hdr_str = ", ".join(f"{h['key']}: {h['value']}" for h in headers)
                        lines.append(f"  请求头: {hdr_str}")
                    else:
                        lines.append("  请求头管理器")
                elif ce.type.value == "CookieManager":
                    lines.append(f"  Cookie管理: 开启 (每次迭代清空: {ce.clearEachIteration})")
                elif ce.type.value == "CacheManager":
                    lines.append(f"  缓存管理: 开启 (使用Expires头: {ce.useExpires})")

            # Scenario-level timers (think time)
            for timer in (scenario.timers or []):
                found = True
                lines.append(f"  思考时间: {self._timer_desc(timer)}")

        if not found:
            lines.append("  无")

        return "\n".join(lines)

    def _listeners(self, ir: IRDocument) -> str:
        """Generate listeners section based on actual IR content."""
        lines = ["【结果收集】"]
        found = False
        for listener in (ir.listeners or []):
            found = True
            name = listener.name or listener.type.value
            if listener.file:
                lines.append(f"  {name} (文件: {listener.file})")
            else:
                lines.append(f"  {name}")
        if not found:
            lines.append("  聚合报告 + 结果文件")
        return "\n".join(lines)

    def _dependency_report(self, issues: list) -> str:
        lines = ["【变量依赖校验】"]
        if not issues:
            lines.append("  ✓ 所有变量引用链完整")
        for issue in issues:
            lines.append(f"  ✗ {issue}")
        return "\n".join(lines)