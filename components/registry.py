"""Component template registry — maps component types to Jinja2 template paths."""

import os
from typing import Dict, List
import yaml


class TemplateRegistry:
    """Maps component type names to Jinja2 template file paths."""

    TEMPLATE_MAP: Dict[str, str] = {
        # P0 核心
        "TestPlan": "TestPlan.xml.j2",
        "ThreadGroup": "ThreadGroup.xml.j2",
        "HTTPSamplerProxy": "samplers/HTTPSamplerProxy.xml.j2",
        "LoopController": "controllers/LoopController.xml.j2",
        "ResponseAssertion": "assertions/ResponseAssertion.xml.j2",
        "DurationAssertion": "assertions/DurationAssertion.xml.j2",
        "JSONExtractor": "extractors/JSONExtractor.xml.j2",
        "RegexExtractor": "extractors/RegexExtractor.xml.j2",
        "UniformRandomTimer": "timers/UniformRandomTimer.xml.j2",
        "ConstantTimer": "timers/ConstantTimer.xml.j2",
        "HeaderManager": "config/HeaderManager.xml.j2",
        "CookieManager": "config/CookieManager.xml.j2",
        "CSVDataSet": "config/CSVDataSet.xml.j2",
        "SummaryReport": "listeners/SummaryReport.xml.j2",
        "SimpleDataWriter": "listeners/SimpleDataWriter.xml.j2",
        # P1 扩展
        "IfController": "controllers/IfController.xml.j2",
        "WhileController": "controllers/WhileController.xml.j2",
        "TransactionController": "controllers/TransactionController.xml.j2",
        "ForEachController": "controllers/ForEachController.xml.j2",
        "JDBCSampler": "samplers/JDBCSampler.xml.j2",
        "TCPSampler": "samplers/TCPSampler.xml.j2",
        "JSR223PreProcessor": "processors/JSR223PreProcessor.xml.j2",
        "JSR223PostProcessor": "processors/JSR223PostProcessor.xml.j2",
        "CounterConfig": "data_sources/CounterConfig.xml.j2",
        "UserParameters": "data_sources/UserParameters.xml.j2",
        "SizeAssertion": "assertions/SizeAssertion.xml.j2",
        "JSONAssertion": "assertions/JSONAssertion.xml.j2",
        "CSSExtractor": "extractors/CSSExtractor.xml.j2",
        "CacheManager": "config/CacheManager.xml.j2",
        "GaussianRandomTimer": "timers/GaussianRandomTimer.xml.j2",
        "AggregateReport": "listeners/AggregateReport.xml.j2",
        "ViewResultsFullVisualizer": "listeners/ViewResultsFullVisualizer.xml.j2",
    }

    def __init__(self, template_dir: str = "components"):
        self.template_dir = template_dir
        self._load_extensions()

    def _load_extensions(self):
        ext_path = os.path.join("extensions", "custom_components.yaml")
        if os.path.exists(ext_path):
            with open(ext_path, encoding="utf-8") as f:
                customs = yaml.safe_load(f) or []
            for comp in customs:
                self.TEMPLATE_MAP[comp["name"]] = comp["template"]

    def get_template_path(self, component_type: str) -> str:
        if component_type not in self.TEMPLATE_MAP:
            raise KeyError(f"No template registered for '{component_type}'")
        return self.TEMPLATE_MAP[component_type]

    def list_available_types(self) -> List[str]:
        return list(self.TEMPLATE_MAP.keys())