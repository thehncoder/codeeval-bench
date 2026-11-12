"""Unit tests for Error Localization and failure diagnosis engine."""

import pytest
from codeeval.core.ast_analyzer import ASTAnalyzer
from codeeval.core.error_localizer import ErrorLocalizer
from codeeval.models import (
    BugType,
    Category,
    Difficulty,
    ExecutionStatus,
    Problem,
    TestCase,
    TestCaseResult,
)


@pytest.fixture
def dummy_problem():
    return Problem(
        id="test-p1",
        title="Test Problem",
        description="A problem for testing diagnosis",
        entry_point="solve",
        category=Category.DATA_STRUCTURES,
        difficulty=Difficulty.EASY,
        golden_solution="def solve(x): return x",
        test_cases=[
            TestCase(inputs={"x": 5}, expected_output=5),
            TestCase(inputs={"x": 10}, expected_output=11),
            TestCase(inputs={"x": []}, expected_output=[]),
        ],
    )


def test_diagnose_off_by_one(dummy_problem):
    ast_metrics = ASTAnalyzer.analyze("def solve(x): return x")
    results = [
        TestCaseResult(
            test_case_idx=1,
            is_hidden=False,
            status=ExecutionStatus.WRONG_ANSWER,
            execution_time_ms=1.0,
            actual_output=10,
            expected_output=11,
            error_message="Wrong Answer",
        )
    ]
    diagnoses = ErrorLocalizer.diagnose_failures(
        problem=dummy_problem,
        candidate_code="def solve(x): return x",
        ast_metrics=ast_metrics,
        results=results,
    )
    assert len(diagnoses) == 1
    assert diagnoses[0].bug_type == BugType.OFF_BY_ONE
    assert "Off-by-one" in diagnoses[0].root_cause_explanation


def test_diagnose_empty_input_failure(dummy_problem):
    ast_metrics = ASTAnalyzer.analyze("def solve(x): return x[0]")
    results = [
        TestCaseResult(
            test_case_idx=2,
            is_hidden=False,
            status=ExecutionStatus.RUNTIME_ERROR,
            execution_time_ms=1.0,
            error_message="IndexError: list index out of range",
            traceback_info='File "test.py", line 1, in solve\n  return x[0]',
        )
    ]
    diagnoses = ErrorLocalizer.diagnose_failures(
        problem=dummy_problem,
        candidate_code="def solve(x): return x[0]",
        ast_metrics=ast_metrics,
        results=results,
    )
    assert len(diagnoses) == 1
    assert diagnoses[0].bug_type == BugType.EMPTY_INPUT_FAILURE
    assert "boundary inputs" in diagnoses[0].root_cause_explanation
