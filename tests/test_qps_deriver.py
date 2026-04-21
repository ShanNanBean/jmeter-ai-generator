"""Tests for QPS deriver."""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.qps_deriver import QPSDeriver


def test_basic_qps_derivation():
    """QPS=500 with default estimates should produce reasonable threads."""
    deriver = QPSDeriver()
    result = deriver.derive(target_qps=500)
    assert result["threads"] >= 10
    assert result["rampUp"] >= 5
    assert result["duration"] == 600
    assert result["loop"] == -1


def test_minimum_threads():
    """Even low QPS should produce at least 10 threads."""
    deriver = QPSDeriver()
    result = deriver.derive(target_qps=1)
    assert result["threads"] >= 10


def test_custom_think_time():
    """Custom think time range should affect thread calculation."""
    deriver = QPSDeriver()
    result_default = deriver.derive(target_qps=100)
    result_fast = deriver.derive(target_qps=100, think_time_range=[100, 200])
    assert result_fast["threads"] < result_default["threads"]