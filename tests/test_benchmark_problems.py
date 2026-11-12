"""Unit tests verifying all benchmark problems and golden reference solutions."""

import pytest
from codeeval.benchmark.registry import BenchmarkRegistry
from codeeval.core.evaluator import CodeEvaluator


def test_registry_loading():
    problems = BenchmarkRegistry.list_all()
    assert len(problems) >= 4
    for p in problems:
        assert p.id
        assert p.title
        assert p.entry_point
        assert len(p.test_cases) >= 3
        assert p.golden_solution


def test_all_golden_solutions_pass():
    problems = BenchmarkRegistry.list_all()
    for p in problems:
        report = CodeEvaluator.evaluate(
            candidate_code=p.golden_solution,
            problem=p,
            model_name="GoldenReference",
        )
        assert report.verdict == "ACCEPTED", f"Problem {p.id} failed verification"
        assert report.passed_tests == report.total_tests
        assert report.rubric_scores.total_score >= 90.0
        assert len(report.diagnoses) == 0
