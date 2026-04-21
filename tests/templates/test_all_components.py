"""Smoke test: all Jinja2 templates render valid XML."""

import pytest
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from jinja2 import Environment, FileSystemLoader, select_autoescape
from components.registry import TemplateRegistry


def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _minimal_context(component_type: str) -> dict:
    """Return minimal context data for each component type."""
    contexts = {
        "TestPlan": {"name": "Test", "serializeThreadGroups": "false", "variables": []},
        "ThreadGroup": {"name": "TG", "threads": 10, "rampUp": 5, "loop": -1},
        "HTTPSamplerProxy": {"name": "Req", "method": "GET", "domain": "example.com", "path": "/api"},
        "LoopController": {"name": "Loop", "loops": 10},
        "ResponseAssertion": {"name": "RA", "pattern": "200", "field": "16", "test_type": 8},
        "DurationAssertion": {"name": "DA", "maxMs": 2000},
        "JSONExtractor": {"variable": "token", "path": "$.data.token", "defaultValue": "NOT_FOUND", "matchNo": 0},
        "RegexExtractor": {"variable": "id", "regex": "id\":\"([^\"]+)\"", "template": "$1$", "defaultValue": "NOT_FOUND", "matchNo": 1},
        "UniformRandomTimer": {"rangeMs": [500, 2000]},
        "ConstantTimer": {"delayMs": 1000},
        "HeaderManager": {"name": "HM", "headers": [{"key": "Content-Type", "value": "application/json"}]},
        "CookieManager": {"name": "CM", "clearEachIteration": "false"},
        "CSVDataSet": {"name": "CSV", "file": "data.csv", "vars": ["user", "pwd"], "delimiter": ","},
        "SummaryReport": {"name": "SR"},
        "SimpleDataWriter": {"name": "SDW", "file": "results.jtl"},
        "IfController": {"name": "If", "condition": "${status} == 200"},
        "WhileController": {"name": "While", "whileCondition": "${__JMeterThreadLastSampleOk()}"},
        "TransactionController": {"name": "TC", "includeTimers": "false"},
        "ForEachController": {"name": "FE", "inputVar": "items", "outputVar": "item"},
        "JDBCSampler": {"name": "JDBC", "dataSource": "db", "query": "SELECT 1"},
        "TCPSampler": {"name": "TCP", "server": "localhost", "port_tcp": 8080},
        "JSR223PreProcessor": {"name": "Pre", "language": "groovy", "script": "vars.put('x','1')", "cacheKey": "true"},
        "JSR223PostProcessor": {"name": "Post", "language": "groovy", "script": "log.info('done')", "cacheKey": "true"},
        "CounterConfig": {"name": "Counter", "variable": "counter", "start": 1, "increment": 1, "end": 999999, "perUser": "false"},
        "UserParameters": {"name": "UP", "parameters": [{"key": "a", "value": "1"}]},
        "SizeAssertion": {"name": "SA", "maxSize": 1000},
        "JSONAssertion": {"name": "JA", "jsonPath": "$.status", "expectedValue": "ok"},
        "CSSExtractor": {"variable": "val", "expression": ".item", "defaultValue": "NOT_FOUND", "matchNo": 0},
        "CacheManager": {"name": "Cache", "clearEachIteration": "false", "useExpires": "true"},
        "GaussianRandomTimer": {"meanMs": 500, "deviationMs": 200},
        "AggregateReport": {"name": "AR"},
        "ViewResultsFullVisualizer": {"name": "VRT"},
    }
    return contexts.get(component_type, {"name": component_type})


@pytest.mark.parametrize("component_type", TemplateRegistry.TEMPLATE_MAP.keys())
def test_template_renders_valid_xml(component_type):
    """Each template should render valid XML with minimal context."""
    project_root = _get_project_root()
    registry = TemplateRegistry(os.path.join(project_root, "components"))
    env = Environment(
        loader=FileSystemLoader(os.path.join(project_root, "components")),
        autoescape=select_autoescape(["xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template_path = registry.get_template_path(component_type)
    template = env.get_template(template_path)

    context = _minimal_context(component_type)
    rendered = template.render(**context)

    # Must be parseable XML
    try:
        elem = ET.fromstring(rendered)
    except ET.ParseError as e:
        pytest.fail(f"Template '{component_type}' renders invalid XML: {e}\nRendered:\n{rendered}")

    # Must have correct testclass attribute (for TestElements)
    testclass = elem.get("testclass", "")
    if testclass:
        # Some JMeter components have different class names vs IR names
        # e.g., JSONExtractor -> JSONPathExtractor, JSONAssertion -> JSONPathAssertion
        known_mappings = {
            "JSONExtractor": "JSONPathExtractor",
            "JSONAssertion": "JSONPathAssertion",
        }
        expected_testclass = known_mappings.get(component_type, component_type)
        # Verify testclass matches (case-insensitive substring check)
        assert (
            testclass.lower() in expected_testclass.lower()
            or expected_testclass.lower() in testclass.lower()
        ), f"Template '{component_type}' has testclass='{testclass}', expected to match '{expected_testclass}'"