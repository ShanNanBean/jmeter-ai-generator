"""JMX Assembler — converts IR into JMeter .jmx XML using Jinja2 templates."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Optional
import yaml
import copy

from jinja2 import Environment, FileSystemLoader
from xml.sax.saxutils import escape as xml_escape

from core.ir_model import (
    IRDocument, StepModel, AssertionModel, ExtractorModel,
    TimerModel, DataSourceModel, ProcessorModel, ControllerModel,
    ConfigElementModel, ListenerModel, ThreadGroupModel, TestPlanModel,
)
from components.registry import TemplateRegistry
from core.path_config import COMPONENTS_DIR, CONFIG_DIR


# Components whose class names differ between JMeter versions
VERSION_SENSITIVE_TYPES = {"JSONExtractor", "CSSExtractor", "JSONAssertion"}

# Default class mappings (JMeter 5.0+, most common)
DEFAULT_CLASS_MAPPINGS = {
    "JSONExtractor": {
        "tag": "JSONPostProcessor",
        "guiclass": "JSONPostProcessorGui",
        "testclass": "JSONPostProcessor",
        "prop_prefix": "JSONPostProcessor",
    },
    "CSSExtractor": {
        "tag": "HtmlExtractor",
        "guiclass": "HtmlExtractorGui",
        "testclass": "HtmlExtractor",
        "prop_prefix": "HtmlExtractor",
    },
    "JSONAssertion": {
        "tag": "JSONPathAssertion",
        "guiclass": "JSONPathAssertionGui",
        "testclass": "JSONPathAssertion",
        "prop_prefix": "JSONPathAssertion",
    },
}


def _load_version_config() -> dict:
    """Load JMeter version compatibility configuration."""
    config_path = CONFIG_DIR / "jmeter_versions.yaml"
    if config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"default": "5.0", "versions": {}}


def _resolve_class_mappings(version: str, version_config: dict) -> dict:
    """Resolve class mappings for a given JMeter version.

    Starts from the base "5.0" mappings and applies version-specific overrides.
    """
    # Start with default mappings
    mappings = copy.deepcopy(DEFAULT_CLASS_MAPPINGS)

    # Apply version-specific overrides
    version_key = version
    if version_key not in version_config.get("versions", {}):
        # Find closest matching version (e.g., "5.6.3" matches "5.6")
        for vk in version_config.get("versions", {}):
            if version.startswith(vk):
                version_key = vk
                break

    version_data = version_config.get("versions", {}).get(version_key, {})
    version_overrides = version_data.get("class_mappings", {})

    # Merge overrides — empty dict means inherit from base
    for comp_type, override in version_overrides.items():
        if override:  # Non-empty override
            mappings[comp_type] = override

    return mappings


def _resolve_jmeter_attrs(version: str, version_config: dict) -> dict:
    """Resolve jmeterTestPlan root element attributes for a given version."""
    version_key = version
    if version_key not in version_config.get("versions", {}):
        for vk in version_config.get("versions", {}):
            if version.startswith(vk):
                version_key = vk
                break

    version_data = version_config.get("versions", {}).get(version_key, {})
    return {
        "jmeter": version_data.get("jmeter", version),
        "properties": version_data.get("properties", "5.0"),
    }


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

    def __init__(self, template_dir: str | None = None, jmeter_version: str = "5.0"):
        template_dir = template_dir or str(COMPONENTS_DIR)
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # We handle XML escaping manually in _sanitize_context
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.registry = TemplateRegistry(template_dir)
        self.jmeter_version = jmeter_version
        self.version_config = _load_version_config()
        self.class_mappings = _resolve_class_mappings(jmeter_version, self.version_config)
        self.jmeter_attrs = _resolve_jmeter_attrs(jmeter_version, self.version_config)

    def assemble(self, ir: IRDocument) -> str:
        """Full assembly: IR -> JMX XML string.

        JMeter .jmx format requires hashTree to be a SIBLING of the
        TestElement, both living inside the parent hashTree.
        """
        root = ET.Element(
            "jmeterTestPlan",
            version="1.2",
            properties=self.jmeter_attrs["properties"],
            jmeter=self.jmeter_attrs["jmeter"],
        )

        # Top-level hashTree under jmeterTestPlan
        top_hash = ET.SubElement(root, "hashTree")

        # TestPlan element (sibling of its hashTree inside top_hash)
        plan_elem = self._render_component("TestPlan", ir.testPlan)
        top_hash.append(plan_elem)
        plan_hash_tree = ET.SubElement(top_hash, "hashTree")

        # Test plan level config elements
        for ce in (ir.configElements or []):
            ce_elem = self._render_component(ce.type.value, ce)
            plan_hash_tree.append(ce_elem)
            ET.SubElement(plan_hash_tree, "hashTree")

        # ThreadGroups
        for tg in ir.threadGroups:
            tg_elem = self._render_threadgroup(tg)
            plan_hash_tree.append(tg_elem)
            tg_hash_tree = ET.SubElement(plan_hash_tree, "hashTree")

            # Find scenarios for this thread group
            for scenario in ir.scenarios:
                if scenario.threadGroup == tg.name:
                    self._add_scenario(tg_hash_tree, scenario)

        # Test plan level listeners
        for listener in (ir.listeners or []):
            l_elem = self._render_component(listener.type.value, listener)
            plan_hash_tree.append(l_elem)
            ET.SubElement(plan_hash_tree, "hashTree")

        return self._serialize(root)

    def _add_scenario(self, parent_hash_tree: ET.Element, scenario):
        """Add a complete scenario to parent hashTree."""
        self._add_scenario_setup(parent_hash_tree, scenario)

        if scenario.controllers:
            for ctrl in scenario.controllers:
                self._render_controller(parent_hash_tree, ctrl, scenario)
        else:
            self._render_steps(parent_hash_tree, scenario.steps)

    def _add_scenario_setup(self, tree: ET.Element, scenario):
        """Render scenario-level setup elements before flow execution."""
        # Data sources
        for ds in (scenario.dataSources or []):
            ds_elem = self._render_component(ds.type.value, ds)
            tree.append(ds_elem)
            ET.SubElement(tree, "hashTree")

        # Config elements
        for ce in (scenario.configElements or []):
            ce_elem = self._render_component(ce.type.value, ce)
            tree.append(ce_elem)
            ET.SubElement(tree, "hashTree")

        # Thread/controller level timers
        for timer in (scenario.timers or []):
            t_elem = self._render_component(timer.type.value, timer)
            tree.append(t_elem)
            ET.SubElement(tree, "hashTree")

    def _populate_scenario_tree(self, tree: ET.Element, scenario):
        """Populate a hashTree with data sources, config, timers, and steps."""
        self._add_scenario_setup(tree, scenario)
        self._render_steps(tree, scenario.steps)

    def _render_steps(self, tree: ET.Element, steps):
        for step in (steps or []):
            self._render_step(tree, step)

    def _render_controller(self, tree: ET.Element, controller: ControllerModel, scenario=None):
        ctrl_elem = self._render_component(controller.type.value, controller)
        tree.append(ctrl_elem)
        ctrl_hash_tree = ET.SubElement(tree, "hashTree")

        has_children = bool(controller.childControllers or controller.childSteps)
        if has_children:
            for child in (controller.childControllers or []):
                self._render_controller(ctrl_hash_tree, child, scenario)
            self._render_steps(ctrl_hash_tree, controller.childSteps)
        elif scenario is not None:
            self._render_steps(ctrl_hash_tree, scenario.steps)

    def _render_step(self, tree: ET.Element, step: StepModel):
        sampler_elem = self._render_component(step.type.value, step)
        tree.append(sampler_elem)
        sampler_hash = ET.SubElement(tree, "hashTree")

        # Pre-processors
        for pre in (step.preProcessors or []):
            pp_elem = self._render_component(pre.type.value, pre)
            sampler_hash.append(pp_elem)
            ET.SubElement(sampler_hash, "hashTree")

        # Post-processors
        for post in (step.postProcessors or []):
            pp_elem = self._render_component(post.type.value, post)
            sampler_hash.append(pp_elem)
            ET.SubElement(sampler_hash, "hashTree")

        # Extractors
        for ext in (step.extractors or []):
            ext_elem = self._render_component(ext.type.value, ext)
            sampler_hash.append(ext_elem)
            ET.SubElement(sampler_hash, "hashTree")

        # Assertions
        for assertion in (step.assertions or []):
            a_elem = self._render_component(assertion.type.value, assertion)
            sampler_hash.append(a_elem)
            ET.SubElement(sampler_hash, "hashTree")

        # Step-level timers
        for timer in (step.timers or []):
            t_elem = self._render_component(timer.type.value, timer)
            sampler_hash.append(t_elem)
            ET.SubElement(sampler_hash, "hashTree")

    def _render_component(self, component_type: str, data) -> ET.Element:
        """Render a component using its Jinja2 template.

        For version-sensitive components, inject version-specific class
        names (tag, guiclass, testclass, prop_prefix) into the template context.
        """
        template_name = self.registry.get_template_path(component_type)
        template = self.jinja_env.get_template(template_name)

        context = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        context = self._apply_defaults(component_type, context)

        # Inject version-specific class mappings for sensitive components
        if component_type in VERSION_SENSITIVE_TYPES:
            mapping = self.class_mappings.get(component_type, DEFAULT_CLASS_MAPPINGS.get(component_type, {}))
            context["tag"] = mapping.get("tag", component_type)
            context["guiclass"] = mapping.get("guiclass", component_type + "Gui")
            context["testclass"] = mapping.get("testclass", component_type)
            context["prop_prefix"] = mapping.get("prop_prefix", component_type)

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
        """Convert Python types to JMX-compatible strings, escaping XML."""
        sanitized = {}
        for key, val in context.items():
            sanitized[key] = self._sanitize_value(val)
        return sanitized

    def _sanitize_value(self, val):
        """Recursively sanitize a value for JMX XML compatibility."""
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, str):
            return xml_escape(val, entities={'"': '&quot;'})
        if isinstance(val, list):
            return [self._sanitize_value(item) for item in val]
        if isinstance(val, dict):
            return {k: self._sanitize_value(v) for k, v in val.items()}
        return val

    def _serialize(self, root: ET.Element) -> str:
        """Serialize XML tree to pretty-printed string."""
        rough_string = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough_string)
        result = parsed.toprettyxml(indent="  ", encoding=None)
        if result.startswith("<?xml"):
            result = result.split("\n", 1)[1]
        return result