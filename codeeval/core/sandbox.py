"""Execution Sandbox for Safe, Timed Evaluation of Candidate Code."""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from codeeval.models import ExecutionStatus, TestCase, TestCaseResult


RUNNER_TEMPLATE = """
import sys
import json
import time
import traceback
import copy

{candidate_code}

def run_test():
    raw_inputs = json.loads({inputs_json!r})
    expected_output = json.loads({expected_json!r})
    entry_point_name = "{entry_point}"

    if entry_point_name not in globals():
        print(json.dumps({{
            "status": "RUNTIME_ERROR",
            "execution_time_ms": 0.0,
            "actual_output": None,
            "error_message": f"Entry point function '{{entry_point_name}}' not found in candidate code.",
            "traceback": ""
        }}))
        return

    func = globals()[entry_point_name]

    start_time = time.perf_counter()
    try:
        # Deepcopy inputs so candidate mutations do not corrupt
        test_args = copy.deepcopy(raw_inputs)
        actual = func(**test_args)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        is_correct = (actual == expected_output)
        status = "PASSED" if is_correct else "WRONG_ANSWER"

        print(json.dumps({{
            "status": status,
            "execution_time_ms": round(elapsed_ms, 3),
            "actual_output": actual,
            "expected_output": expected_output,
            "error_message": None if is_correct else "Output does not match expected reference value.",
            "traceback": None
        }}))
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        tb = traceback.format_exc()
        print(json.dumps({{
            "status": "RUNTIME_ERROR",
            "execution_time_ms": round(elapsed_ms, 3),
            "actual_output": None,
            "expected_output": expected_output,
            "error_message": f"{{type(e).__name__}}: {{str(e)}}",
            "traceback": tb
        }}))

if __name__ == "__main__":
    run_test()
"""


class Sandbox:
    """Executes candidate code against test cases in an isolated sub-process with timeouts."""

    @classmethod
    def execute_test_case(
        cls,
        candidate_code: str,
        entry_point: str,
        test_case: TestCase,
        index: int,
    ) -> TestCaseResult:
        inputs_json = json.dumps(test_case.inputs)
        expected_json = json.dumps(test_case.expected_output)

        runner_script = RUNNER_TEMPLATE.format(
            candidate_code=candidate_code,
            inputs_json=inputs_json,
            expected_json=expected_json,
            entry_point=entry_point,
        )

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_path = temp_file.name
            temp_file.write(runner_script)

        try:
            start_wall = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=test_case.timeout_seconds,
            )
            elapsed_wall_ms = (time.perf_counter() - start_wall) * 1000.0

            if proc.returncode != 0:
                # Script crashed before generating json
                stderr_text = proc.stderr.strip()
                return TestCaseResult(
                    test_case_idx=index,
                    is_hidden=test_case.is_hidden,
                    status=ExecutionStatus.RUNTIME_ERROR,
                    execution_time_ms=round(elapsed_wall_ms, 3),
                    actual_output=None,
                    expected_output=test_case.expected_output,
                    error_message=f"Process exited with code {proc.returncode}: {stderr_text[:300]}",
                    traceback_info=stderr_text,
                )

            stdout_text = proc.stdout.strip()
            # Find the JSON line in case student code printed logs
            json_line = None
            for line in reversed(stdout_text.splitlines()):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    json_line = line
                    break

            if not json_line:
                return TestCaseResult(
                    test_case_idx=index,
                    is_hidden=test_case.is_hidden,
                    status=ExecutionStatus.RUNTIME_ERROR,
                    execution_time_ms=round(elapsed_wall_ms, 3),
                    actual_output=None,
                    expected_output=test_case.expected_output,
                    error_message=f"Invalid output format: {stdout_text[:200]}",
                    traceback_info=proc.stderr,
                )

            data = json.loads(json_line)
            return TestCaseResult(
                test_case_idx=index,
                is_hidden=test_case.is_hidden,
                status=ExecutionStatus(data["status"]),
                execution_time_ms=data["execution_time_ms"],
                actual_output=data.get("actual_output"),
                expected_output=test_case.expected_output,
                error_message=data.get("error_message"),
                traceback_info=data.get("traceback"),
            )

        except subprocess.TimeoutExpired:
            return TestCaseResult(
                test_case_idx=index,
                is_hidden=test_case.is_hidden,
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                execution_time_ms=round(test_case.timeout_seconds * 1000.0, 3),
                actual_output=None,
                expected_output=test_case.expected_output,
                error_message=f"Execution timed out after {test_case.timeout_seconds}s limit",
                traceback_info=None,
            )
        except Exception as e:
            return TestCaseResult(
                test_case_idx=index,
                is_hidden=test_case.is_hidden,
                status=ExecutionStatus.RUNTIME_ERROR,
                execution_time_ms=0.0,
                actual_output=None,
                expected_output=test_case.expected_output,
                error_message=str(e),
                traceback_info=None,
            )
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
