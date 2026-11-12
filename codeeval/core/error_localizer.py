"""Error Localization & Failure Diagnosis Engine for Code Evaluation."""

import re
from typing import List, Optional
from codeeval.models import (
    ASTMetrics,
    BugDiagnosis,
    BugType,
    ExecutionStatus,
    Problem,
    TestCase,
    TestCaseResult,
)


class ErrorLocalizer:
    """Pinpoints failure line numbers, classifies bug types, and generates actionable critiques."""

    @classmethod
    def diagnose_failures(
        cls,
        problem: Problem,
        candidate_code: str,
        ast_metrics: ASTMetrics,
        results: List[TestCaseResult],
    ) -> List[BugDiagnosis]:
        diagnoses: List[BugDiagnosis] = []
        failing_results = [r for r in results if r.status != ExecutionStatus.PASSED]

        if not failing_results:
            return diagnoses

        # 1. Syntax check
        if not ast_metrics.syntax_valid:
            diagnoses.append(
                BugDiagnosis(
                    line_number=ast_metrics.syntax_error_line,
                    bug_type=BugType.SYNTAX_OR_IMPORT,
                    root_cause_explanation=f"Syntax Error: {ast_metrics.syntax_error}",
                    failing_input_summary="N/A (Code failed compilation)",
                    suggested_fix="Fix syntax syntax errors at the specified line before re-evaluating.",
                )
            )
            return diagnoses

        # 2. Check for Timeouts (Asymptotic Complexity)
        timeouts = [r for r in failing_results if r.status == ExecutionStatus.TIME_LIMIT_EXCEEDED]
        if timeouts:
            t = timeouts[0]
            tc = problem.test_cases[t.test_case_idx]
            diag = cls._diagnose_timeout(problem, ast_metrics, tc)
            diagnoses.append(diag)

        # 3. Check Runtime Errors (Exceptions, Recursion, Empty Inputs)
        runtime_errs = [r for r in failing_results if r.status == ExecutionStatus.RUNTIME_ERROR]
        for r in runtime_errs[:2]:  # Keep top 2 unique
            tc = problem.test_cases[r.test_case_idx]
            diag = cls._diagnose_runtime_error(candidate_code, r, tc)
            if not any(d.root_cause_explanation == diag.root_cause_explanation for d in diagnoses):
                diagnoses.append(diag)

        # 4. Check Wrong Answers (Off-by-one, boundary cases, logical errors)
        wrong_answers = [r for r in failing_results if r.status == ExecutionStatus.WRONG_ANSWER]
        for r in wrong_answers[:2]:
            tc = problem.test_cases[r.test_case_idx]
            diag = cls._diagnose_wrong_answer(candidate_code, r, tc)
            if not any(d.root_cause_explanation == diag.root_cause_explanation for d in diagnoses):
                diagnoses.append(diag)

        return diagnoses

    @classmethod
    def _diagnose_timeout(
        cls,
        problem: Problem,
        ast_metrics: ASTMetrics,
        test_case: TestCase,
    ) -> BugDiagnosis:
        loop_depth = ast_metrics.max_loop_nesting
        explanation = (
            f"Execution exceeded time limit on large benchmark inputs. "
            f"Detected loop nesting depth of {loop_depth}, suggesting potential "
            f"O(N^{loop_depth if loop_depth > 1 else 2}) complexity instead of required optimal bound."
        )
        return BugDiagnosis(
            line_number=None,
            bug_type=BugType.ASYMPTOTIC_TIMEOUT,
            root_cause_explanation=explanation,
            failing_input_summary=f"Input description: {test_case.description or 'Large scale test case'}",
            suggested_fix=(
                "Refactor algorithmic approach from brute-force / nested iterations to "
                "hash-map indexing, two-pointers, binary search, or dynamic programming memoization."
            ),
        )

    @classmethod
    def _diagnose_runtime_error(
        cls,
        candidate_code: str,
        result: TestCaseResult,
        test_case: TestCase,
    ) -> BugDiagnosis:
        tb = result.traceback_info or ""
        error_msg = result.error_message or "Unknown runtime exception"

        # Extract line number from candidate code in traceback
        line_num = None
        matches = re.findall(r'File ".*?", line (\d+)', tb)
        if matches:
            line_num = int(matches[-1])

        # Check for empty input failure
        has_empty = any(v == [] or v == "" or v == {} for v in test_case.inputs.values())
        if ("IndexError" in error_msg or "KeyError" in error_msg) and has_empty:
            return BugDiagnosis(
                line_number=line_num,
                bug_type=BugType.EMPTY_INPUT_FAILURE,
                root_cause_explanation=(
                    f"Unhandled edge case: accessing index/key on empty collection ({error_msg}). "
                    f"Candidate fails to guard against boundary inputs."
                ),
                failing_input_summary=str(test_case.inputs),
                suggested_fix="Add an early exit guard clause at function entry: e.g., if not input_data: return default_value",
            )

        # Check for recursion limit
        if "RecursionError" in error_msg:
            return BugDiagnosis(
                line_number=line_num,
                bug_type=BugType.RECURSION_DEPTH_EXCEEDED,
                root_cause_explanation="Exceeded Python recursion depth limit (1000). Lack of memoization or unhandled cyclic state.",
                failing_input_summary=str(test_case.inputs),
                suggested_fix="Convert recursive formulation into an iterative table or use functools.lru_cache with depth check.",
            )

        return BugDiagnosis(
            line_number=line_num,
            bug_type=BugType.LOGICAL_FLAW,
            root_cause_explanation=f"Runtime exception during execution: {error_msg}",
            failing_input_summary=str(test_case.inputs),
            suggested_fix="Inspect variable state at the failing line and ensure proper type and boundary checking.",
        )

    @classmethod
    def _diagnose_wrong_answer(
        cls,
        candidate_code: str,
        result: TestCaseResult,
        test_case: TestCase,
    ) -> BugDiagnosis:
        actual = result.actual_output
        expected = result.expected_output

        # Detect numerical off-by-one
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            diff = actual - expected
            if abs(diff) == 1:
                direction = "higher" if diff > 0 else "lower"
                return BugDiagnosis(
                    line_number=None,
                    bug_type=BugType.OFF_BY_ONE,
                    root_cause_explanation=(
                        f"Off-by-one error detected: candidate produced {actual}, which is exactly 1 {direction} "
                        f"than expected {expected}. Commonly caused by range boundaries (0-indexing vs 1-indexing) or inclusive vs exclusive interval bounds."
                    ),
                    failing_input_summary=str(test_case.inputs),
                    suggested_fix="Check range() limits or <= vs < comparison operators in loop conditions and base cases.",
                )

        # Detect list off-by-one (e.g. missing 1 element or 1 extra element)
        if isinstance(actual, list) and isinstance(expected, list):
            if len(actual) == len(expected) - 1:
                return BugDiagnosis(
                    line_number=None,
                    bug_type=BugType.OFF_BY_ONE,
                    root_cause_explanation=(
                        f"Array length mismatch: candidate returned {len(actual)} elements, missing the boundary element (expected {len(expected)})."
                    ),
                    failing_input_summary=str(test_case.inputs),
                    suggested_fix="Ensure loop termination conditions evaluate the final boundary element (e.g., range(n + 1)).",
                )

        return BugDiagnosis(
            line_number=None,
            bug_type=BugType.LOGICAL_FLAW,
            root_cause_explanation=(
                f"Logical divergence: candidate output {repr(actual)} deviates from expected {repr(expected)} "
                f"for scenario '{test_case.description or 'Custom Edge Case'}'."
            ),
            failing_input_summary=str(test_case.inputs),
            suggested_fix="Audit state transitions, accumulator updates, and conditional branching against the problem invariants.",
        )
