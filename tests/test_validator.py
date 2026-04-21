"""Tests for JMX validator."""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.validator import JMXValidator, ValidationResult


def test_invalid_xml():
    """Invalid XML should be caught."""
    validator = JMXValidator()
    result = validator.validate("<invalid><unclosed>")
    assert not result.valid
    assert any(i.severity == "error" and i.category == "structure" for i in result.issues)


def test_valid_simple_jmx():
    """A valid minimal JMX should pass."""
    jmx = """<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test" enabled="true">
    <boolProp name="TestPlan.functional_mode">false</boolProp>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="TG" enabled="true">
        <stringProp name="ThreadGroup.num_threads">10</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Req" enabled="true">
            <stringProp name="HTTPSampler.domain">example.com</stringProp>
            <stringProp name="HTTPSampler.path">/api</stringProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <hashTree/>
          </HTTPSamplerProxy>
        </hashTree>
      </ThreadGroup>
    </hashTree>
  </TestPlan>
</jmeterTestPlan>"""

    validator = JMXValidator()
    result = validator.validate(jmx)
    assert result.valid


def test_missing_hashtree():
    """A TestElement without hashTree should be flagged."""
    jmx = """<jmeterTestPlan version="1.2">
  <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Test" enabled="true">
    <boolProp name="TestPlan.functional_mode">false</boolProp>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="TG" enabled="true">
        <stringProp name="ThreadGroup.num_threads">10</stringProp>
        <hashTree/>
      </ThreadGroup>
    </hashTree>
  </TestPlan>
</jmeterTestPlan>"""

    # This JMX is valid — ThreadGroup has hashTree
    validator = JMXValidator()
    result = validator.validate(jmx)
    assert result.valid