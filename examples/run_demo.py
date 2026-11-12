"""Interactive Demonstration Script for CodeEval-Bench.
Evaluates a flawed LLM candidate submission against the Constrained Subsequence Sum problem,
pinpointing bugs, calculating frontier rubric scores, and generating an audit report.
"""

from pathlib import Path
from codeeval.benchmark.registry import BenchmarkRegistry
from codeeval.core.evaluator import CodeEvaluator
from codeeval.reporting.exporters import ReportExporter


def run_demo():
    print("=" * 70)
    print("   CodeEval-Bench: LLM Code & Reasoning Evaluation Demo")
    print("=" * 70)

    problem_id = "eval-dp-001"
    problem = BenchmarkRegistry.get_by_id(problem_id)
    submission_path = Path(__file__).parent / "sample_submissions" / "faulty_gpt4_dp.py"

    print(f"\n[1] Target Benchmark Problem: {problem.title} [{problem.id}]")
    print(f"    Difficulty: {problem.difficulty.value} | Category: {problem.category.value}")
    print(f"    Test Cases: {len(problem.test_cases)} total ({sum(1 for t in problem.test_cases if t.is_hidden)} hidden)")

    print(f"\n[2] Evaluating Candidate Submission: {submission_path.name}")
    code_text = submission_path.read_text(encoding="utf-8")

    report = CodeEvaluator.evaluate(
        candidate_code=code_text,
        problem=problem,
        model_name="Simulated-GPT4-Candidate",
    )

    print("\n[3] Frontier Evaluation Rubric Audit:")
    print(f"    - Final Verdict:            {report.verdict}")
    print(f"    - Overall Score:            {report.rubric_scores.total_score} / 100.0")
    print(f"    - Tests Passed:             {report.passed_tests} / {report.total_tests} ({report.accuracy_percentage}%)")
    print(f"    - Hidden Test Resilience:   {report.hidden_tests_passed} / {report.hidden_tests_total}")
    print(f"    - Correctness Dimension:    {report.rubric_scores.correctness_score} / 40.0")
    print(f"    - Edge-Case Resilience:     {report.rubric_scores.edge_case_resilience} / 30.0")
    print(f"    - Code Quality (AST):       {report.rubric_scores.code_quality_and_ast} / 15.0")
    print(f"    - Time Efficiency:          {report.rubric_scores.time_complexity_score} / 15.0")

    print("\n[4] Detected Flaws & Diagnoses:")
    for idx, diag in enumerate(report.diagnoses, 1):
        line = f"Line {diag.line_number}" if diag.line_number else "Algorithmic Scope"
        print(f"    [{idx}] {diag.bug_type} ({line})")
        print(f"        Cause: {diag.root_cause_explanation}")
        print(f"        Fix:   {diag.suggested_fix}")

    report_out = Path(__file__).parent / "evaluation_report_demo.md"
    md_content = ReportExporter.to_markdown(report, problem)
    report_out.write_text(md_content, encoding="utf-8")
    print(f"\n[5] Generated Full Evaluation Audit Markdown: {report_out.name}")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
