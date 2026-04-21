"""Scenario Preview Generator — generates human-readable pseudo-script from IR."""

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

        # Section 2: Thread group params
        sections.append(self._thread_params(ir))

        # Section 3: Business flow
        sections.append(self._flow(ir))

        # Section 4: Data sources
        sections.append(self._data_sources(ir))

        # Section 5: Global config
        sections.append(self._global_config(ir))

        # Section 6: Result collection
        sections.append(self._listeners(ir))

        # Section 7: Variable dependency check
        dep_issues = self.dep_checker.check(ir)
        sections.append(self._dependency_report(dep_issues))

        return "\n\n".join(sections)

    def _header(self, ir: IRDocument) -> str:
        name = ir.testPlan.name
        return f"压测场景预览 — {name}\n{'=' * 50}"

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

                step_num += 1
        return "\n".join(lines)

    def _data_sources(self, ir: IRDocument) -> str:
        lines = ["【数据源】"]
        for scenario in ir.scenarios:
            for ds in (scenario.dataSources or []):
                if ds.type.value == "CSVDataSet":
                    vars_str = ",".join(ds.vars or [])
                    lines.append(f"  CSV: {ds.file} (字段: {vars_str})")
                elif ds.type.value == "CounterConfig":
                    lines.append(f"  计数器: {ds.variable} ({ds.start}→∞)")
        if len(lines) == 1:
            lines.append("  无")
        return "\n".join(lines)

    def _global_config(self, ir: IRDocument) -> str:
        lines = ["【全局配置】"]
        lines.append("  Cookie管理: 开启")
        lines.append("  超时设置: 连接5s, 响应10s")
        lines.append("  思考时间: 0.5~2秒随机")
        return "\n".join(lines)

    def _listeners(self, ir: IRDocument) -> str:
        lines = ["【结果收集】"]
        for listener in (ir.listeners or []):
            name = listener.name or listener.type.value
            lines.append(f"  {name}")
        if len(lines) == 1:
            lines.append("  聚合报告 + 结果文件")
        return "\n".join(lines)

    def _dependency_report(self, issues: list) -> str:
        lines = ["【变量依赖校验】"]
        if not issues:
            lines.append("  ✓ 所有变量引用链完整")
        for issue in issues:
            lines.append(f"  ✗ {issue}")
        return "\n".join(lines)