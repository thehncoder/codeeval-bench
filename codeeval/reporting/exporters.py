"""Report Exporters: Generates Detailed Markdown and JSON Evaluation Audits."""

import json
from codeeval.models import EvaluationReport, Problem


class ReportExporter:
    """Exports structured evaluation reports into GitHub-flavored Markdown or JSON."""

    @classmethod
    def to_markdown(cls, report: EvaluationReport, problem: Problem) -> str:
        verdict_badge = {
            "ACCEPTED": "🟢 **ACCEPTED (Production Grade)**",
            "PARTIAL": "🟡 **PARTIAL (Edge-Case Vulnerabilities)**",
            "REJECTED": "🔴 **REJECTED (Correctness / Safety Failure)**",
        }.get(report.verdict, report.verdict)

        md = []
        md.append(f"# AI Model Evaluation Report: `{report.problem_id}`")
        md.append("")
        md.append(f"**Target Problem:** {report.problem_title}  ")
        md.append(f"**Evaluated Model / Submission:** `{report.model_name}`  ")
        md.append(f"**Final Verdict:** {verdict_badge}  ")
        md.append(f"**Overall Rubric Score:** `{report.rubric_scores.total_score} / 100.0`  ")
        md.append(f"**Evaluation Timestamp:** {report.generated_at}  ")
        md.append("")
        md.append("---")
        md.append("")

        # Section 1: Rubric Breakdown
        md.append("## 1. Frontier Evaluation Rubric Breakdown")
        md.append("")
        md.append("| Evaluation Dimension | Score | Max Points | Weight / Focus |")
        md.append("| :--- | :---: | :---: | :--- |")
        md.append(f"| **Correctness & Output Fidelity** | `{report.rubric_scores.correctness_score}` | 40.0 | Overall test suite accuracy ({report.passed_tests}/{report.total_tests} passed) |")
        md.append(f"| **Edge-Case & Boundary Resilience** | `{report.rubric_scores.edge_case_resilience}` | 30.0 | Hidden tests ({report.hidden_tests_passed}/{report.hidden_tests_total} passed) |")
        md.append(f"| **Code Quality & AST Hygiene** | `{report.rubric_scores.code_quality_and_ast}` | 15.0 | Complexity, recursion, and anti-pattern penalties |")
        md.append(f"| **Asymptotic Time Efficiency** | `{report.rubric_scores.time_complexity_score}` | 15.0 | Algorithmic scaling within time limit ({problem.time_limit_seconds}s) |")
        md.append(f"| **TOTAL SCORE** | **`{report.rubric_scores.total_score}`** | **100.0** | **Verdict: {report.verdict}** |")
        md.append("")

        # Section 2: AST Analysis
        md.append("## 2. AST Static Analysis & Code Structure")
        md.append("")
        ast = report.ast_metrics
        md.append(f"- **Syntax Validity:** {'✅ Valid' if ast.syntax_valid else '❌ Syntax Error'}")
        if not ast.syntax_valid:
            md.append(f"  - *Error:* `{ast.syntax_error}` at line {ast.syntax_error_line}")
        md.append(f"- **Cyclomatic Complexity:** `{ast.cyclomatic_complexity}`")
        md.append(f"- **Max Loop Nesting Depth:** `{ast.max_loop_nesting}`")
        md.append(f"- **Recursive Call Detected:** `{'Yes' if ast.has_recursion else 'No'}`")
        if ast.detected_antipatterns:
            md.append("- **Detected Anti-patterns / Smells:**")
            for ap in ast.detected_antipatterns:
                md.append(f"  - ⚠️ {ap}")
        else:
            md.append("- **Detected Anti-patterns:** None (Clean static structure)")
        md.append("")

        # Section 3: Test Results Table
        md.append("## 3. Test Case Execution Matrix")
        md.append("")
        md.append("| # | Type | Description | Status | Execution Time | Notes / Error |")
        md.append("| :-: | :-: | :--- | :-: | :-: | :--- |")
        for r in report.test_results:
            tag = "🔒 Hidden" if r.is_hidden else "🌐 Public"
            status_icon = "✅ PASSED" if r.status == "PASSED" else f"❌ `{r.status}`"
            note = r.error_message or "Matches expected output"
            if len(note) > 60:
                note = note[:57] + "..."
            tc_desc = problem.test_cases[r.test_case_idx].description or f"Test Case #{r.test_case_idx + 1}"
            md.append(f"| {r.test_case_idx + 1} | {tag} | {tc_desc} | {status_icon} | {r.execution_time_ms} ms | {note} |")
        md.append("")

        # Section 4: Diagnoses & Error Localization
        md.append("## 4. Root Cause Diagnosis & Error Localization")
        md.append("")
        if not report.diagnoses:
            md.append("🎉 **No bugs identified.** The candidate implementation satisfied all public and hidden boundary invariants.")
        else:
            for idx, diag in enumerate(report.diagnoses, 1):
                loc = f"Line {diag.line_number}" if diag.line_number else "Global / Algorithmic Scope"
                md.append(f"### Bug #{idx}: `{diag.bug_type}` ({loc})")
                md.append(f"- **Root Cause:** {diag.root_cause_explanation}")
                md.append(f"- **Failing Inputs:** `{diag.failing_input_summary}`")
                md.append(f"- **Recommended Fix:** {diag.suggested_fix}")
                md.append("")

        # Section 5: Golden Reference Solution
        md.append("## 5. Verified Golden Reference Solution")
        md.append("")
        md.append("Below is the benchmark reference solution meeting set quality, asymptotic, and boundary standards:")
        md.append("")
        md.append("```python")
        md.append(problem.golden_solution)
        md.append("```")
        md.append("")

        return "\n".join(md)

    @classmethod
    def to_json(cls, report: EvaluationReport) -> str:
        return report.model_dump_json(indent=2)
