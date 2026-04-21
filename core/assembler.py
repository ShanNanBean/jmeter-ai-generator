"""JMX Assembler — converts IR into JMeter .jmx XML using Jinja2 templates."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.ir_model import (
    IRDocument, StepModel, AssertionModel, ExtractorModel,
    TimerModel, DataSourceModel, ProcessorModel, ControllerModel,
    ConfigElementModel, ListenerModel, ThreadGroupModel, TestPlanModel,
)
from components.registry import TemplateRegistry


class JMXAssembler:
    """Assembles IR into JMX XML using Jinja2 component templates."""

    NESTING_RULES = {
        "CounterConfig": ["thread_group", "controller"],
        "CSVDataSet": ["thread_group", "controller"],
        "UserParameters": ["thread_group", "controller"],
        "JSR223PreProcessor": ["sampler"],
        "JSR223PostProcessor": ["sampler"],
        "RegexExtractor": ["sampler"],
        "JSONExtractor": ["sampler"],
        "CSSExtractor": ["sampler"],
        "ResponseAssertion": ["sampler"],
        "DurationAssertion": ["sampler"],
        "SizeAssertion": ["sampler"],
        "JSONAssertion": ["sampler"],
        "UniformRandomTimer": ["thread_group", "controller", "sampler"],
        "ConstantTimer": ["thread_group", "controller", "sampler"],
        "GaussianRandomTimer": ["thread_group", "controller", "sampler"],
        "HeaderManager": ["sampler", "thread_group", "test_plan"],
        "CookieManager": ["sampler", "thread_group"],
        "CacheManager": ["sampler", "thread_group"],
        "TransactionController": ["thread_group"],
        "IfController": ["thread_group", "controller"],
        "WhileController": ["thread_group", "controller"],
        "ForEachController": ["thread_group", "controller"],
    }

    def __init__(self, template_dir: str = "components"):
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Add custom filters for JMX compatibility
        self.jinja_env.filters["jmx_bool"] = self._jmx_bool
        self.jinja_env.filters["jmx_str"] = self._jmx_str
        self.registry = TemplateRegistry(template_dir)

    def assemble(self, ir: IRDocument) -> str:
        """Full assembly: IR -> JMX XML string."""
        root = ET.Element(
            "jmeterTestPlan",
            version="1.2",
            properties="5.0",
            jmeter="5.6.3",
        )

        # TestPlan + hashTree
        plan_elem = self._render_component("TestPlan", ir.testPlan)
        root.append(plan_elem)
        plan_hash_tree = ET.SubElement(plan_elem, "hashTree")

        # Test plan level config elements
        for ce in (ir.configElements or []):
            ce_elem = self._render_component(ce.type.value, ce)
            plan_hash_tree.append(ce_elem)
            ET.SubElement(ce_elem, "hashTree")

        # ThreadGroups
        for tg in ir.threadGroups:
            tg_elem = self._render_threadgroup(tg)
            plan_hash_tree.append(tg_elem)
            tg_hash_tree = ET.SubElement(tg_elem, "hashTree")

            # Find scenarios for this thread group
            for scenario in ir.scenarios:
                if scenario.threadGroup == tg.name:
                    self._add_scenario(tg_hash_tree, scenario)

        # Test plan level listeners
        for listener in (ir.listeners or []):
            l_elem = self._render_component(listener.type.value, listener)
            plan_hash_tree.append(l_elem)
            ET.SubElement(l_elem, "hashTree")

        return self._serialize(root)

    def _add_scenario(self, parent_hash_tree: ET.Element, scenario):
        """Add a complete scenario to parent hashTree."""
        # If there's a controller, wrap steps inside it
        if scenario.controllers:
            for ctrl in scenario.controllers:
                ctrl_elem = self._render_component(ctrl.type.value, ctrl)
                parent_hash_tree.append(ctrl_elem)
                ctrl_hash_tree = ET.SubElement(ctrl_elem, "hashTree")
                self._populate_scenario_tree(ctrl_hash_tree, scenario)
        else:
            self._populate_scenario_tree(parent_hash_tree, scenario)

    def _populate_scenario_tree(self, tree: ET.Element, scenario):
        """Populate a hashTree with data sources, config, timers, and steps."""
        # Data sources
        for ds in (scenario.dataSources or []):
            ds_elem = self._render_component(ds.type.value, ds)
            tree.append(ds_elem)
            ET.SubElement(ds_elem, "hashTree")

        # Config elements
        for ce in (scenario.configElements or []):
            ce_elem = self._render_component(ce.type.value, ce)
            tree.append(ce_elem)
            ET.SubElement(ce_elem, "hashTree")

        # Thread/controller level timers
        for timer in (scenario.timers or []):
            t_elem = self._render_component(timer.type.value, timer)
            tree.append(t_elem)
            ET.SubElement(t_elem, "hashTree")

        # Steps (samplers)
        for step in scenario.steps:
            sampler_elem = self._render_component(step.type.value, step)
            tree.append(sampler_elem)
            sampler_tree = ET.SubElement(sampler_elem, "hashTree")

            # Pre-processors
            for pre in (step.preProcessors or []):
                pp_elem = self._render_component(pre.type.value, pre)
                sampler_tree.append(pp_elem)
                ET.SubElement(pp_elem, "hashTree")

            # Post-processors
            for post in (step.postProcessors or []):
                pp_elem = self._render_component(post.type.value, post)
                sampler_tree.append(pp_elem)
                ET.SubElement(pp_elem, "hashTree")

            # Extractors
            for ext in (step.extractors or []):
                ext_elem = self._render_component(ext.type.value, ext)
                sampler_tree.append(ext_elem)
                ET.SubElement(ext_elem, "hashTree")

            # Assertions
            for assertion in (step.assertions or []):
                a_elem = self._render_component(assertion.type.value, assertion)
                sampler_tree.append(a_elem)
                ET.SubElement(a_elem, "hashTree")

            # Step-level timers
            for timer in (step.timers or []):
                t_elem = self._render_component(timer.type.value, timer)
                sampler_tree.append(t_elem)
                ET.SubElement(t_elem, "hashTree")

    def _render_component(self, component_type: str, data) -> ET.Element:
        """Render a component using its Jinja2 template."""
        template_name = self.registry.get_template_path(component_type)
        template = self.jinja_env.get_template(template_name)

        context = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        context = self._apply_defaults(component_type, context)

        rendered_xml = template.render(**context)
        return ET.fromstring(rendered_xml)

    def _render_threadgroup(self, tg: ThreadGroupModel) -> ET.Element:
        return self._render_component("ThreadGroup", tg)

    def _apply_defaults(self, component_type: str, context: dict) -> dict:
        """Apply required defaults for template rendering and fix types."""
        defaults = {
            "HTTPSamplerProxy": {
                "port": "",
                "protocol": "https",
                "method": "GET",
                "contentEncoding": "utf-8",
            },
            "ThreadGroup": {
                "onSampleError": "continue",
                "sameUserOnNextIteration": True,
            },
            "LoopController": {"continueForever": False},
        }
        if component_type in defaults:
            for key, val in defaults[component_type].items():
                if key not in context or context[key] is None:
                    context[key] = val

        # Sanitize all values for JMX compatibility
        context = self._sanitize_context(context)
        return context

    def _sanitize_context(self, context: dict) -> dict:
        """Convert Python types to JMX-compatible strings."""
        sanitized = {}
        for key, val in context.items():
            sanitized[key] = self._jmx_str(val)
        return sanitized

    @staticmethod
    def _jmx_bool(val) -> str:
        """Convert Python bool to JMX string 'true'/'false'."""
        if isinstance(val, bool):
            return "true" if val else "false"
        return str(val)

    @staticmethod
    def _jmx_str(val) -> str:
        """Convert value to JMX-compatible string."""
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, list):
            return val  # Lists are handled by templates
        return val

    def _serialize(self, root: ET.Element) -> str:
        """Serialize XML tree to pretty-printed string."""
        rough_string = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough_string)
        result = parsed.toprettyxml(indent="  ", encoding=None)
        # Remove the XML declaration that minidom adds (JMeter expects no declaration)
        if result.startswith("<?xml"):
            result = result.split("\n", 1)[1]
        return result