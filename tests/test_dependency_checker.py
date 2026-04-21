"""Tests for dependency checker."""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.ir_model import (
    IRDocument, TestPlanModel, ThreadGroupModel, ScenarioModel,
    StepModel, ExtractorModel, DataSourceModel, VariableModel,
)
from core.dependency_checker import DependencyChecker


def test_valid_forward_reference():
    """Extractor defines variable, next step references it — OK."""
    checker = DependencyChecker()
    ir = IRDocument(
        testPlan=TestPlanModel(name="test"),
        threadGroups=[ThreadGroupModel(name="tg")],
        scenarios=[
            ScenarioModel(
                name="sc",
                threadGroup="tg",
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="step1",
                        path="/login",
                        extractors=[ExtractorModel(type="JSONExtractor", variable="token", path="$.token")],
                    ),
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="step2",
                        path="/profile",
                        headers=[{"key": "Auth", "value": "${token}"}],
                    ),
                ],
            )
        ],
    )
    issues = checker.check(ir)
    assert len(issues) == 0


def test_broken_reference():
    """Step references undefined variable — should flag issue."""
    checker = DependencyChecker()
    ir = IRDocument(
        testPlan=TestPlanModel(name="test"),
        threadGroups=[ThreadGroupModel(name="tg")],
        scenarios=[
            ScenarioModel(
                name="sc",
                threadGroup="tg",
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="step1",
                        path="/profile",
                        headers=[{"key": "Auth", "value": "${undefined_var}"}],
                    ),
                ],
            )
        ],
    )
    issues = checker.check(ir)
    assert len(issues) > 0
    assert "undefined_var" in issues[0]


def test_csv_variables_available():
    """CSV variables should be available from step 1."""
    checker = DependencyChecker()
    ir = IRDocument(
        testPlan=TestPlanModel(name="test"),
        threadGroups=[ThreadGroupModel(name="tg")],
        scenarios=[
            ScenarioModel(
                name="sc",
                threadGroup="tg",
                dataSources=[DataSourceModel(type="CSVDataSet", file="users.csv", vars=["user", "pwd"])],
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="step1",
                        path="/login",
                        body='{"username": "${user}"}',
                    ),
                ],
            )
        ],
    )
    issues = checker.check(ir)
    assert len(issues) == 0


def test_testplan_variables_available():
    """Test plan variables should be available from step 1."""
    checker = DependencyChecker()
    ir = IRDocument(
        testPlan=TestPlanModel(
            name="test",
            variables=[VariableModel(key="base_url", value="https://api.example.com")],
        ),
        threadGroups=[ThreadGroupModel(name="tg")],
        scenarios=[
            ScenarioModel(
                name="sc",
                threadGroup="tg",
                steps=[
                    StepModel(
                        type="HTTPSamplerProxy",
                        name="step1",
                        domain="${base_url}",
                        path="/api",
                    ),
                ],
            )
        ],
    )
    issues = checker.check(ir)
    assert len(issues) == 0