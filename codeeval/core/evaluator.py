"""Evaluation Coordinator: Orchestrates AST Analysis, Sandbox Execution, and Rubric Generation."""

from datetime import datetime, timezone
from typing import List, Optional
from codeeval.benchmark.registry import BenchmarkRegistry
from codeeval.core.ast_analyzer import ASTAnalyzer
from codeeval.core.error_localizer import ErrorLocalizer
from codeeval.core.sandbox import Sandbox
from codeeval.models import (
    EvaluationReport,
    ExecutionStatus,
    Problem,
    TestCaseResult,
)
from codeeval.reporting.rubric import RubricCalculator


class CodeEvaluator:
    """End-to-end evaluation harness for auditing AI candidate code against benchmark problems."""

    @classmethod
    def evaluate(
        cls,
        candidate_code: str,
        problem: Problem,
        model_name: str = "Candidate-Model",
    ) -> EvaluationReport:
        # 1. AST Analysis
        ast_metrics = ASTAnalyzer.analyze(candidate_code)

        results: List[TestCaseResult] = []

        if not ast_metrics.syntax_valid:
            # Syntax failure: mark all test cases as syntax errors
            for idx, tc in enumerate(problem.test_cases):
                results.append(
                    TestCaseResult(
                        test_case_idx=idx,
                        is_hidden=tc.is_hidden,
                        status=ExecutionStatus.SYNTAX_ERROR,
                        execution_time_ms=0.0,
                        actual_output=None,
                        expected_output=tc.expected_output,
                        error_message=f"Syntax Error: {ast_metrics.syntax_error} (line {ast_metrics.syntax_error_line})",
                    )
                )
        else:
            # 2. Sandbox Execution across all test cases
            for idx, tc in enumerate(problem.test_cases):
                res = Sandbox.execute_test_case(
                    candidate_code=candidate_code,
                    entry_point=problem.entry_point,
                    test_case=tc,
                    index=idx,
                )
                results.append(res)

        # 3. Bug Diagnosis & Error Localization
        diagnoses = ErrorLocalizer.diagnose_failures(
            problem=problem,
            candidate_code=candidate_code,
            ast_metrics=ast_metrics,
            results=results,
        )

        # 4. Rubric Scoring
        rubric_scores = RubricCalculator.calculate_scores(results, ast_metrics)
        verdict = RubricCalculator.determine_verdict(rubric_scores)

        # 5. Metrics Aggregation
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ExecutionStatus.PASSED)
        hidden_tests = [r for r in results if r.is_hidden]
        hidden_passed = sum(1 for r in hidden_tests if r.status == ExecutionStatus.PASSED)
        accuracy = round((passed_tests / total_tests) * 100.0, 2) if total_tests > 0 else 0.0

        return EvaluationReport(
            problem_id=problem.id,
            problem_title=problem.title,
            model_name=model_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            hidden_tests_total=len(hidden_tests),
            hidden_tests_passed=hidden_passed,
            accuracy_percentage=accuracy,
            verdict=verdict,
            ast_metrics=ast_metrics,
            test_results=results,
            diagnoses=diagnoses,
            rubric_scores=rubric_scores,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
