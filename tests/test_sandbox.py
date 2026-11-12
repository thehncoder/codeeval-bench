"""Unit tests for subprocess execution sandbox and safety isolation."""

import pytest
from codeeval.core.sandbox import Sandbox
from codeeval.models import ExecutionStatus, TestCase


def test_sandbox_success():
    code = """
def compute(x, y):
    return x * 2 + y
"""
    tc = TestCase(inputs={"x": 5, "y": 3}, expected_output=13)
    res = Sandbox.execute_test_case(code, "compute", tc, 0)
    assert res.status == ExecutionStatus.PASSED
    assert res.actual_output == 13
    assert res.execution_time_ms >= 0


def test_sandbox_wrong_answer():
    code = """
def compute(x, y):
    return x + y
"""
    tc = TestCase(inputs={"x": 5, "y": 3}, expected_output=13)
    res = Sandbox.execute_test_case(code, "compute", tc, 0)
    assert res.status == ExecutionStatus.WRONG_ANSWER
    assert res.actual_output == 8
    assert res.expected_output == 13


def test_sandbox_runtime_exception():
    code = """
def compute(x, y):
    return x / y
"""
    tc = TestCase(inputs={"x": 10, "y": 0}, expected_output=0)
    res = Sandbox.execute_test_case(code, "compute", tc, 0)
    assert res.status == ExecutionStatus.RUNTIME_ERROR
    assert "ZeroDivisionError" in (res.error_message or "")


def test_sandbox_timeout():
    code = """
import time
def slow_loop(n):
    time.sleep(2.0)
    return n
"""
    tc = TestCase(inputs={"n": 42}, expected_output=42, timeout_seconds=0.5)
    res = Sandbox.execute_test_case(code, "slow_loop", tc, 0)
    assert res.status == ExecutionStatus.TIME_LIMIT_EXCEEDED
    assert "timed out" in (res.error_message or "").lower()


def test_sandbox_missing_entry_point():
    code = """
def other_name(x):
    return x
"""
    tc = TestCase(inputs={"x": 1}, expected_output=1)
    res = Sandbox.execute_test_case(code, "target_func", tc, 0)
    assert res.status == ExecutionStatus.RUNTIME_ERROR
    assert "not found" in (res.error_message or "").lower()
