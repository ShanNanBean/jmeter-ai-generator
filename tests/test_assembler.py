"""Tests for JMX assembler."""

import pytest
import xml.etree.ElementTree as ET
import os
import sys
import json

# Project root is one level up from tests/
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from core.ir_model import IRDocument, TestPlanModel, ThreadGroupModel, ScenarioModel, StepModel
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