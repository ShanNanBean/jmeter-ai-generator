"""Tests for JMX assembler."""

import pytest
import xml.etree.ElementTree as ET
import os
import sys
import json

# Project root is one level up from tests/
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from core.ir_model import (
    IRDocument,
    TestPlanModel,
    ThreadGroupModel,
    ScenarioModel,
    StepModel,
    ComponentType,
    AssertionModel,
    DataSourceModel,
    ProcessorModel,
    ControllerModel,
    ExtractorModel,
)
from core.assembler import JMXAssembler


def _get_assembler():
    template_dir = os.path.join(PROJECT_ROOT, "components")
    return JMXAssembler(template_dir)


def _simple_ir():
    return IRDocument(
        testPlan=TestPlanModel(name="简单测试", variables=[]),
        threadGroups=[ThreadGroupModel(name="用户组", threads=10, rampUp=5, duration=60, loop=-1)],
        scenarios=[
            ScenarioModel(
                name="登录流程",
                threadGroup="用户组",
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="登录请求",
                        method="POST",
                        path="/api/login",
                        body='{"username": "${user}"}',
                    )
                ],
            )
        ],
    )


def test_assemble_simple_ir():
    """Test that a simple IR produces valid JMX XML."""
    assembler = _get_assembler()
    ir = _simple_ir()
    jmx = assembler.assemble(ir)

    # Must be parseable XML
    root = ET.fromstring(jmx)
    assert root.tag == "jmeterTestPlan"

    # Structure: jmeterTestPlan > hashTree > TestPlan + hashTree(sibling)
    top_hash = root.find("hashTree")
    assert top_hash is not None

    # Must contain TestPlan as child of top hashTree
    testplans = top_hash.findall("TestPlan")
    assert len(testplans) == 1
    assert testplans[0].get("testname") == "简单测试"

    # TestPlan's sibling hashTree must contain ThreadGroup
    # In JMeter format: hashTree children are TestPlan followed by hashTree(sibling)
    plan_ht = top_hash.findall("hashTree")[0]
    thread_groups = plan_ht.findall("ThreadGroup")
    assert len(thread_groups) == 1
    assert thread_groups[0].get("testname") == "用户组"


def test_assemble_has_htree_sibling_nesting():
    """Test that every TestElement has a hashTree sibling within the parent hashTree.

    JMeter requires hashTree to be a SIBLING of the TestElement,
    both direct children of the parent hashTree.
    """
    assembler = _get_assembler()
    ir = _simple_ir()
    jmx = assembler.assemble(ir)

    root = ET.fromstring(jmx)

    # Verify the sibling pattern: each TestElement is followed by a hashTree
    # at the same level within its parent hashTree.
    # Check ThreadGroup has a sibling hashTree inside plan hashTree
    plan_ht = root.find("hashTree/hashTree")
    assert plan_ht is not None
    children = list(plan_ht)
    # Children should alternate: TestElement, hashTree, TestElement, hashTree, ...
    tg_idx = next(i for i, c in enumerate(children) if c.tag == "ThreadGroup")
    # Next sibling must be hashTree
    assert children[tg_idx + 1].tag == "hashTree"

    # Check HTTPSamplerProxy has a sibling hashTree inside TG hashTree
    tg_ht = children[tg_idx + 1]
    sampler_idx = next(i for i, c in enumerate(list(tg_ht)) if c.tag == "HTTPSamplerProxy")
    sampler_children = list(tg_ht)
    assert sampler_children[sampler_idx + 1].tag == "hashTree"


def test_misplaced_timer_step_is_normalized_to_scenario_timer():
    """LLM output may place timer objects in steps; normalize them before step validation."""
    ir_dict = {
        "testPlan": {"name": "timer test"},
        "threadGroups": [{"name": "users", "threads": 1, "rampUp": 1}],
        "scenarios": [
            {
                "name": "flow",
                "threadGroup": "users",
                "steps": [
                    {"type": "HTTPSamplerProxy", "name": "request", "path": "/api"},
                    {"type": "ConstantTimer", "delayMs": 100},
                ],
            }
        ],
    }

    ir = IRDocument.model_validate(ir_dict)

    assert len(ir.scenarios[0].steps) == 1
    assert ir.scenarios[0].timers is not None
    assert ir.scenarios[0].timers[0].type == ComponentType.CONSTANT_TIMER
    assert ir.scenarios[0].timers[0].delayMs == 100

def test_templates_emit_jmeter_gui_safe_property_types():
    assembler = _get_assembler()
    ir = IRDocument(
        testPlan=TestPlanModel(name="safe props"),
        threadGroups=[ThreadGroupModel(name="users", threads=1, rampUp=1, duration=None, delay=None)],
        scenarios=[
            ScenarioModel(
                name="flow",
                threadGroup="users",
                dataSources=[DataSourceModel(type="CSVDataSet", file="users.csv", vars=["user"])],
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="request",
                        path="/api",
                        assertions=[
                            AssertionModel(type="DurationAssertion"),
                            AssertionModel(type="SizeAssertion"),
                            AssertionModel(type="ResponseAssertion", pattern="200"),
                        ],
                        preProcessors=[ProcessorModel(type="JSR223PreProcessor", script="")],
                        postProcessors=[ProcessorModel(type="JSR223PostProcessor", script="")],
                    )
                ],
            )
        ],
    )

    root = ET.fromstring(assembler.assemble(ir))
    thread_group = root.find(".//ThreadGroup")
    csv = root.find(".//CSVDataSet")
    pre_processor = root.find(".//JSR223PreProcessor")
    post_processor = root.find(".//JSR223PostProcessor")

    assert thread_group.find("stringProp[@name='ThreadGroup.duration']").text == "0"
    assert thread_group.find("stringProp[@name='ThreadGroup.delay']").text == "0"
    assert csv.find("boolProp[@name='quotedData']").text == "false"
    assert pre_processor.get("guiclass") == "TestBeanGUI"
    assert post_processor.get("guiclass") == "TestBeanGUI"
    assert pre_processor.find("boolProp[@name='cacheKey']").text == "true"
    assert post_processor.find("boolProp[@name='cacheKey']").text == "true"
    assert root.find(".//collectionProp[@name='Assertion.test_strings']") is not None
    assert root.find(".//stringProp[@name='DurationAssertion.duration']").text == "3000"
    assert root.find(".//stringProp[@name='Assertion.expected_size']").text == "1024"


def test_nested_controller_children_render_without_flat_step_duplication():
    assembler = _get_assembler()
    ir = IRDocument(
        testPlan=TestPlanModel(name="nested controllers"),
        threadGroups=[ThreadGroupModel(name="users", threads=1, rampUp=1)],
        scenarios=[
            ScenarioModel(
                name="batch upload",
                threadGroup="users",
                steps=[
                    StepModel(type="HTTPSamplerProxy", name="legacy flat step", path="/legacy"),
                ],
                controllers=[
                    ControllerModel(
                        type="WhileController",
                        name="Upload pressure loop",
                        whileCondition="${__groovy(true)}",
                        childControllers=[
                            ControllerModel(
                                type="IfController",
                                name="Need new batch",
                                condition='${__groovy(vars.get("needBatch") != "false")}',
                                childSteps=[
                                    StepModel(
                                        type="HTTPSamplerProxy",
                                        name="Create batch",
                                        method="POST",
                                        path="/scan-batch",
                                    )
                                ],
                            )
                        ],
                        childSteps=[
                            StepModel(
                                type="HTTPSamplerProxy",
                                name="Upload paper",
                                method="POST",
                                path="/paper",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    root = ET.fromstring(assembler.assemble(ir))
    samplers = root.findall(".//HTTPSamplerProxy")
    assert [sampler.get("testname") for sampler in samplers] == ["Create batch", "Upload paper"]

    while_controller = root.find(".//WhileController")
    assert while_controller is not None
    plan_ht = root.find("hashTree/hashTree/hashTree")
    children = list(plan_ht)
    while_idx = next(i for i, child in enumerate(children) if child is while_controller)
    while_hash = children[while_idx + 1]
    assert while_hash.tag == "hashTree"
    assert while_hash.find("IfController") is not None
    assert while_hash.find("HTTPSamplerProxy[@testname='Upload paper']") is not None


def test_batch_upload_flow_primitives_render_in_controller_tree():
    ordinal_script = """
if (vars.get('batchId') == null || vars.get('scanOrdinal') == null || vars.get('scanOrdinal') as int >= 300) {
    vars.put('needBatch', 'true')
    vars.put('scanOrdinal', '0')
}
vars.put('scanOrdinal', (((vars.get('scanOrdinal') ?: '0') as int) + 1).toString())
""".strip()
    upload_body = """{
    "batchId": "${batchId}",
    "scanOrdinal": ${scanOrdinal}
}"""
    assembler = _get_assembler()
    ir = IRDocument(
        testPlan=TestPlanModel(name="batch flow"),
        threadGroups=[ThreadGroupModel(name="users", threads=50, rampUp=30, duration=600)],
        scenarios=[
            ScenarioModel(
                name="flow",
                threadGroup="users",
                dataSources=[DataSourceModel(type="CSVDataSet", file="exam-ids.csv", vars=["examId", "schoolId", "token"])],
                steps=[],
                controllers=[
                    ControllerModel(
                        type="WhileController",
                        name="Upload pressure loop",
                        whileCondition="${__groovy(true)}",
                        childControllers=[
                            ControllerModel(
                                type="IfController",
                                name="Need new batch",
                                condition='${__groovy(vars.get("needBatch") != "false")}',
                                childSteps=[
                                    StepModel(
                                        type="HTTPSamplerProxy",
                                        name="Create batch",
                                        method="POST",
                                        domain="test-yj.xkw.com",
                                        protocol="https",
                                        path="/api/marking-exam-manager/tiny-client/scan-batch",
                                        params=[{"name": "examId", "value": "${examId}"}],
                                        extractors=[ExtractorModel(type="JSONExtractor", variable="batchId", path="$.data.batchId")],
                                    )
                                ],
                            )
                        ],
                        childSteps=[
                            StepModel(
                                type="HTTPSamplerProxy",
                                name="Upload paper",
                                method="POST",
                                domain="yuejuan.xkw.com",
                                protocol="https",
                                path="/api/marking-exam-manager/tiny-client/paper",
                                body=upload_body,
                                preProcessors=[ProcessorModel(type="JSR223PreProcessor", script=ordinal_script)],
                            )
                        ],
                    )
                ],
            )
        ],
    )

    root = ET.fromstring(assembler.assemble(ir))
    create_batch = root.find(".//HTTPSamplerProxy[@testname='Create batch']")
    upload_paper = root.find(".//HTTPSamplerProxy[@testname='Upload paper']")
    assert create_batch is not None
    assert upload_paper is not None
    assert create_batch.find("stringProp[@name='HTTPSampler.domain']").text == "test-yj.xkw.com"
    assert upload_paper.find("stringProp[@name='HTTPSampler.domain']").text == "yuejuan.xkw.com"
    assert root.find(".//stringProp[@name='JSONPostProcessor.referenceNames']").text == "batchId"
    assert root.find(".//stringProp[@name='JSONPostProcessor.jsonPathExprs']").text == "$.data.batchId"

    body = upload_paper.find(".//stringProp[@name='Argument.value']").text
    assert "${batchId}" in body
    assert "${scanOrdinal}" in body

    script = root.find(".//JSR223PreProcessor/stringProp[@name='script']").text
    assert "scanOrdinal" in script
    assert "300" in script
    assert "needBatch" in script


def test_controller_only_scenario_does_not_require_flat_steps():
    ir = IRDocument.model_validate(
        {
            "testPlan": {"name": "controller only"},
            "threadGroups": [{"name": "users", "threads": 1, "rampUp": 1}],
            "scenarios": [
                {
                    "name": "flow",
                    "threadGroup": "users",
                    "controllers": [
                        {
                            "type": "WhileController",
                            "name": "loop",
                            "whileCondition": "${__groovy(true)}",
                            "childSteps": [
                                {"type": "HTTPSamplerProxy", "name": "request", "path": "/api"}
                            ],
                        }
                    ],
                }
            ],
        }
    )

    assert ir.scenarios[0].steps == []
    root = ET.fromstring(_get_assembler().assemble(ir))
    assert root.find(".//WhileController") is not None
    assert root.find(".//HTTPSamplerProxy[@testname='request']") is not None


def test_assemble_with_fixture():
    """Test assembling from fixture IR JSON."""
    fixture_path = os.path.join(PROJECT_ROOT, "tests/fixtures/sample_ir_simple.json")
    with open(fixture_path, encoding="utf-8") as f:
        ir_dict = json.load(f)

    ir = IRDocument.model_validate(ir_dict)
    assembler = _get_assembler()
    jmx = assembler.assemble(ir)

    root = ET.fromstring(jmx)
    assert root.tag == "jmeterTestPlan"

    # Should have HTTPSamplerProxy
    samplers = root.findall(".//HTTPSamplerProxy")
    assert len(samplers) > 0