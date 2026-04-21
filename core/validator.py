"""JMX Validator — validates generated JMX files for correctness."""

import xml.etree.ElementTree as ET
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    severity: str  # "error", "warning", "info"
    category: str  # "structure", "semantic", "reference"
    message: str
    location: Optional[str] = None


@dataclass
class ValidationResult:
    valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    def add_issue(self, severity: str, category: str, message: str, location: str = None):
        self.issues.append(ValidationIssue(severity, category, message, location))
        if severity == "error":
            self.valid = False


PROPERTY_TAGS = {
    "stringProp", "boolProp", "intProp", "longProp",
    "floatProp", "doubleProp", "elementProp", "collectionProp", "mapProp",
}

REQUIRED_PROPERTIES = {
    "HTTPSamplerProxy": {"HTTPSampler.domain", "HTTPSampler.path", "HTTPSampler.method"},
    "ThreadGroup": {"ThreadGroup.num_threads", "ThreadGroup.ramp_time"},
    "JSONPathExtractor": {"JSONPathExtractor.referenceNames", "JSONPathExtractor.jsonPathExprs"},
    "RegexExtractor": {"RegexExtractor.refname", "RegexExtractor.regex"},
    "CSVDataSet": {"file", "variableNames"},
}


class JMXValidator:
    """Validates generated JMX files for structural and semantic correctness."""

    def validate(self, jmx_str: str) -> ValidationResult:
        result = ValidationResult()

        # Phase 1: XML parsing
        try:
            root = ET.fromstring(jmx_str)
        except ET.ParseError as e:
            result.add_issue("error", "structure", f"Invalid XML: {e}")
            return result

        # Phase 2: hashTree nesting
        self._check_hashtree_nesting(root, result)

        # Phase 3: Required properties
        self._check_required_properties(root, result)

        # Phase 4: Semantic rules
        self._check_threadgroup_has_content(root, result)

        return result

    def _check_hashtree_nesting(self, root: ET.Element, result: ValidationResult):
        """Every TestElement must have a hashTree child element."""
        for elem in root.iter():
            # Skip property elements and hashTree itself
            if elem.tag in PROPERTY_TAGS or elem.tag in {"hashTree", "jmeterTestPlan"}:
                continue
            # Only check elements that look like JMeter TestElements (have testclass or guiclass)
            if elem.get("testclass") or elem.get("guiclass"):
                # Must have at least one hashTree child
                hash_tree_children = [c for c in elem if c.tag == "hashTree"]
                if not hash_tree_children:
                    result.add_issue(
                        "warning", "structure",
                        f"Element '{elem.tag}' has no hashTree child",
                        location=elem.get("testname", elem.tag),
                    )

    def _check_required_properties(self, root: ET.Element, result: ValidationResult):
        """Verify required properties exist for key components."""
        for elem in root.iter():
            testclass = elem.get("testclass", "")
            if testclass in REQUIRED_PROPERTIES:
                found_props = set()
                for prop_elem in elem.iter():
                    if prop_elem.tag in {"stringProp", "boolProp", "intProp"}:
                        name = prop_elem.get("name", "")
                        if name:
                            found_props.add(name)
                for req in REQUIRED_PROPERTIES[testclass]:
                    if req not in found_props:
                        result.add_issue(
                            "warning", "semantic",
                            f"Component '{testclass}' missing property '{req}'",
                            location=elem.get("testname", testclass),
                        )

    def _check_threadgroup_has_content(self, root: ET.Element, result: ValidationResult):
        """ThreadGroup hashTree must contain at least one sampler or controller."""
        for tg in root.iter("ThreadGroup"):
            tg_name = tg.get("testname", "")
            # Find parent to locate sibling hashTree
            parent_map = {c: p for p in root.iter() for c in p}
            if tg in parent_map:
                parent = parent_map[tg]
                siblings = list(parent)
                tg_idx = siblings.index(tg)
                if tg_idx + 1 < len(siblings) and siblings[tg_idx + 1].tag == "hashTree":
                    ht = siblings[tg_idx + 1]
                    has_content = any(
                        c.tag != "hashTree" and c.tag not in PROPERTY_TAGS
                        for c in ht
                    )
                    if not has_content:
                        result.add_issue(
                            "warning", "semantic",
                            f"ThreadGroup '{tg_name}' has no samplers or controllers",
                            location=tg_name,
                        )