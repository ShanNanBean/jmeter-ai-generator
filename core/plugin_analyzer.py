"""Plugin dependency and compatibility hints for generated JMeter plans."""

from typing import Any, Dict, List

from core.ir_model import IRDocument


class PluginAnalyzer:
    """Reports plugin requirements or recommendations without blocking generation."""

    PLUGIN_COMPONENTS = {
        "ConcurrencyThreadGroup": "Custom Thread Groups",
        "ThroughputShapingTimer": "Throughput Shaping Timer",
        "UltimateThreadGroup": "Custom Thread Groups",
        "SteppingThreadGroup": "Custom Thread Groups",
    }

    def analyze(self, ir: IRDocument) -> List[Dict[str, Any]]:
        infos: List[Dict[str, Any]] = []
        used_types = self._collect_component_types(ir)

        for component, plugin_name in self.PLUGIN_COMPONENTS.items():
            if component in used_types:
                infos.append({
                    "name": plugin_name,
                    "required": True,
                    "description": f"脚本中使用了 {component}，运行前需要在 JMeter 安装对应插件。",
                    "component": component,
                    "severity": "warning",
                })

        if not infos and self._looks_like_precise_qps_plan(ir):
            infos.append({
                "name": "Throughput Shaping Timer / Custom Thread Groups",
                "required": False,
                "description": "当前脚本使用 JMeter 原生线程组近似实现压测目标；如果需要精准 QPS 或阶梯升压，后续可安装插件并补充对应模板。",
                "component": None,
                "severity": "info",
            })

        if not infos:
            infos.append({
                "name": "JMeter 原生组件",
                "required": False,
                "description": "当前脚本未检测到第三方插件依赖，可优先用原生 JMeter 打开和运行。",
                "component": None,
                "severity": "info",
            })

        return infos

    def _collect_component_types(self, ir: IRDocument) -> set[str]:
        types = set()
        for scenario in ir.scenarios:
            for ctrl in scenario.controllers or []:
                types.add(ctrl.type.value)
            for timer in scenario.timers or []:
                types.add(timer.type.value)
            for step in scenario.steps:
                types.add(step.type.value)
                for timer in step.timers or []:
                    types.add(timer.type.value)
                for assertion in step.assertions or []:
                    types.add(assertion.type.value)
                for extractor in step.extractors or []:
                    types.add(extractor.type.value)
        return types

    def _looks_like_precise_qps_plan(self, ir: IRDocument) -> bool:
        total_threads = sum(tg.threads for tg in ir.threadGroups)
        return total_threads >= 100 or len(ir.threadGroups) > 1
