"""Command-Line Interface (CLI) for CodeEval-Bench."""

import argparse
import sys
from pathlib import Path
from codeeval.benchmark.registry import BenchmarkRegistry
from codeeval.core.evaluator import CodeEvaluator
from codeeval.reporting.exporters import ReportExporter


def format_table(headers, rows):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(cell)))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_lines = [
        " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        for row in rows
    ]
    return f"{header_line}\n{sep_line}\n" + "\n".join(row_lines)


def cmd_list_problems(args):
    problems = BenchmarkRegistry.list_all()
    print(f"\nLoaded {len(problems)} Frontier Benchmark Problems:\n")
    headers = ["ID", "Title", "Category", "Difficulty", "Tests (Public/Hidden)"]
    rows = []
    for p in problems:
        hidden = sum(1 for t in p.test_cases if t.is_hidden)
        public = len(p.test_cases) - hidden
        rows.append([
            p.id,
            p.title[:38] + ("..." if len(p.title) > 38 else ""),
            p.category.value,
            p.difficulty.value,
            f"{len(p.test_cases)} ({public}/{hidden})",
        ])
    print(format_table(headers, rows))
    print()


def cmd_verify_golden(args):
    problems = BenchmarkRegistry.list_all()
    print(f"\nVerifying {len(problems)} Golden Solutions for Benchmark Integrity...\n")
    all_passed = True

    for p in problems:
        report = CodeEvaluator.evaluate(
            candidate_code=p.golden_solution,
            problem=p,
            model_name="GoldenReference",
        )
        if report.verdict == "ACCEPTED" and report.passed_tests == report.total_tests:
            print(f"  [PASS] {p.id}: {p.title} ({report.passed_tests}/{report.total_tests} tests)")
        else:
            print(f"  [FAIL] {p.id}: {p.title} - Score {report.rubric_scores.total_score}")
            all_passed = False

    if all_passed:
        print("\nAll golden reference solutions passed verification. Benchmark integrity confirmed.\n")
    else:
        print("\nSome golden solutions failed. Please inspect benchmark tests.\n")
        sys.exit(1)


def cmd_eval(args):
    problem = BenchmarkRegistry.get_by_id(args.problem)
    if not problem:
        print(f"Error: Problem ID '{args.problem}' not found in registry.")
        sys.exit(1)

    code_path = Path(args.file)
    if not code_path.exists():
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    candidate_code = code_path.read_text(encoding="utf-8")
    model_name = args.model or code_path.stem

    print(f"\nRunning CodeEval on '{args.file}' for Problem [{problem.id}]...")
    report = CodeEvaluator.evaluate(
        candidate_code=candidate_code,
        problem=problem,
        model_name=model_name,
    )

    print("\n" + "=" * 60)
    print(f"  EVALUATION RESULTS: {report.model_name}")
    print("=" * 60)
    print(f"  Problem:         {report.problem_title} ({report.problem_id})")
    print(f"  Verdict:         {report.verdict}")
    print(f"  Overall Score:   {report.rubric_scores.total_score} / 100.0")
    print(f"  Tests Passed:    {report.passed_tests} / {report.total_tests} ({report.accuracy_percentage}%)")
    print(f"  Hidden Tests:    {report.hidden_tests_passed} / {report.hidden_tests_total}")
    print("-" * 60)
    print("  Frontier Rubric Breakdown:")
    print(f"    - Correctness:           {report.rubric_scores.correctness_score} / 40.0")
    print(f"    - Edge-Case Resilience:  {report.rubric_scores.edge_case_resilience} / 30.0")
    print(f"    - Code Quality (AST):    {report.rubric_scores.code_quality_and_ast} / 15.0")
    print(f"    - Time Efficiency:       {report.rubric_scores.time_complexity_score} / 15.0")
    print("-" * 60)

    if report.diagnoses:
        print(f"  Detected Flaws ({len(report.diagnoses)}):")
        for idx, d in enumerate(report.diagnoses, 1):
            line_str = f"Line {d.line_number}" if d.line_number else "Algorithmic Scope"
            print(f"    [{idx}] {d.bug_type} ({line_str}):")
            print(f"        {d.root_cause_explanation}")
            print(f"        Fix: {d.suggested_fix}")
    else:
        print("  Detected Flaws: None. Solution passed all rigorous tests.")
    print("=" * 60 + "\n")

    if args.out_md:
        md_text = ReportExporter.to_markdown(report, problem)
        Path(args.out_md).write_text(md_text, encoding="utf-8")
        print(f"Saved Markdown report to: {args.out_md}")

    if args.out_json:
        json_text = ReportExporter.to_json(report)
        Path(args.out_json).write_text(json_text, encoding="utf-8")
        print(f"Saved JSON report to: {args.out_json}")


def main():
    parser = argparse.ArgumentParser(
        prog="codeeval",
        description="CodeEval-Bench: LLM Code Generation & Reasoning Evaluation Framework",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-problems
    p_list = subparsers.add_parser("list-problems", help="List all benchmark challenge problems")
    p_list.set_defaults(func=cmd_list_problems)

    # verify-golden
    p_verify = subparsers.add_parser("verify-golden", help="Verify benchmark integrity using golden solutions")
    p_verify.set_defaults(func=cmd_verify_golden)

    # eval
    p_eval = subparsers.add_parser("eval", help="Evaluate a candidate code file against a problem")
    p_eval.add_argument("--problem", "-p", required=True, help="Problem ID (e.g., eval-dp-001)")
    p_eval.add_argument("--file", "-f", required=True, help="Path to Python file containing solution")
    p_eval.add_argument("--model", "-m", help="Model / submission label")
    p_eval.add_argument("--out-md", help="Path to output markdown report")
    p_eval.add_argument("--out-json", help="Path to output JSON report")
    p_eval.set_defaults(func=cmd_eval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
