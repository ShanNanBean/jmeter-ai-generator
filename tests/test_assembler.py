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

    # Must contain TestPlan
    testplans = root.findall("TestPlan")
    assert len(testplans) == 1
    assert testplans[0].get("testname") == "简单测试"

    # TestPlan must have hashTree child
    hash_trees = testplans[0].findall("hashTree")
    assert len(hash_trees) >= 1

    # hashTree must contain ThreadGroup
    plan_ht = hash_trees[0]
    thread_groups = plan_ht.findall("ThreadGroup")
    assert len(thread_groups) == 1
    assert thread_groups[0].get("testname") == "用户组"


def test_assemble_has_htree_nesting():
    """Test that every TestElement has a hashTree child."""
    assembler = _get_assembler()
    ir = _simple_ir()
    jmx = assembler.assemble(ir)

    root = ET.fromstring(jmx)
    # Check ThreadGroup has hashTree child
    tg = root.find(".//ThreadGroup")
    assert tg is not None
    ht = tg.find("hashTree")
    assert ht is not None

    # Check HTTPSamplerProxy has hashTree child
    sampler = root.find(".//HTTPSamplerProxy")
    assert sampler is not None
    ht2 = sampler.find("hashTree")
    assert ht2 is not None


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