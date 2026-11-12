"""Frontier AI Lab Rubric Scoring Engine for Code Evaluation."""

from typing import List
from codeeval.models import (
    ASTMetrics,
    ExecutionStatus,
    RubricScores,
    TestCaseResult,
)


class RubricCalculator:
    """Calculates granular, multi-dimensional rubric scores matching frontier evaluation criteria."""

    @classmethod
    def calculate_scores(
        cls,
        results: List[TestCaseResult],
        ast_metrics: ASTMetrics,
    ) -> RubricScores:
        if not results or not ast_metrics.syntax_valid:
            return RubricScores(
                correctness_score=0.0,
                edge_case_resilience=0.0,
                code_quality_and_ast=0.0,
                time_complexity_score=0.0,
            )

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ExecutionStatus.PASSED)
        hidden_tests = [r for r in results if r.is_hidden]
        hidden_passed = sum(1 for r in hidden_tests if r.status == ExecutionStatus.PASSED)

        # 1. Correctness Score (Max 40)
        correctness = round((passed_tests / total_tests) * 40.0, 2)

        # 2. Edge Case Resilience (Max 30)
        if hidden_tests:
            edge_resilience = round((hidden_passed / len(hidden_tests)) * 30.0, 2)
        else:
            edge_resilience = 30.0

        # 3. Code Quality & AST Metrics (Max 15)
        quality = 15.0
        # Deduct for anti-patterns
        quality -= len(ast_metrics.detected_antipatterns) * 3.0
        # Deduct for extreme cyclomatic complexity
        if ast_metrics.cyclomatic_complexity > 15:
            quality -= 4.0
        elif ast_metrics.cyclomatic_complexity > 10:
            quality -= 2.0
        quality = max(0.0, min(15.0, round(quality, 2)))

        # 4. Time Complexity & Efficiency (Max 15)
        efficiency = 15.0
        has_tle = any(r.status == ExecutionStatus.TIME_LIMIT_EXCEEDED for r in results)
        if has_tle:
            efficiency = 0.0
        else:
            # Check for excessive nesting that hints at quadratic/cubic behavior
            if ast_metrics.max_loop_nesting >= 3:
                efficiency -= 5.0
            efficiency = max(0.0, min(15.0, round(efficiency, 2)))

        return RubricScores(
            correctness_score=correctness,
            edge_case_resilience=edge_resilience,
            code_quality_and_ast=quality,
            time_complexity_score=efficiency,
        )

    @classmethod
    def determine_verdict(cls, rubric: RubricScores) -> str:
        total = rubric.total_score
        if total >= 90.0:
            return "ACCEPTED"
        elif total >= 50.0:
            return "PARTIAL"
        return "REJECTED"
