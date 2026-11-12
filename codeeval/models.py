"""Data models and schemas for CodeEval-Bench."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    FRONTIER = "FRONTIER"


class Category(str, Enum):
    DYNAMIC_PROGRAMMING = "DYNAMIC_PROGRAMMING"
    GRAPH_ALGORITHMS = "GRAPH_ALGORITHMS"
    STRING_PARSING = "STRING_PARSING"
    CONCURRENCY_ASYNC = "CONCURRENCY_ASYNC"
    MATH_NUMBER_THEORY = "MATH_NUMBER_THEORY"
    DATA_STRUCTURES = "DATA_STRUCTURES"


class TestCase(BaseModel):
    __test__ = False
    inputs: Dict[str, Any]
    expected_output: Any
    is_hidden: bool = False
    timeout_seconds: float = 2.0
    description: str = ""


class Problem(BaseModel):
    id: str
    title: str
    description: str
    entry_point: str
    category: Category
    difficulty: Difficulty
    constraints: List[str] = Field(default_factory=list)
    time_limit_seconds: float = 2.0
    memory_limit_mb: float = 256.0
    test_cases: List[TestCase] = Field(default_factory=list)
    golden_solution: str
    common_pitfalls: List[str] = Field(default_factory=list)


class ASTMetrics(BaseModel):
    syntax_valid: bool = True
    syntax_error: Optional[str] = None
    syntax_error_line: Optional[int] = None
    has_recursion: bool = False
    max_loop_nesting: int = 0
    cyclomatic_complexity: int = 1
    detected_antipatterns: List[str] = Field(default_factory=list)


class ExecutionStatus(str, Enum):
    PASSED = "PASSED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"


class TestCaseResult(BaseModel):
    __test__ = False
    test_case_idx: int
    is_hidden: bool
    status: ExecutionStatus
    execution_time_ms: float
    actual_output: Any = None
    expected_output: Any = None
    error_message: Optional[str] = None
    traceback_info: Optional[str] = None


class BugType(str, Enum):
    OFF_BY_ONE = "OFF_BY_ONE"
    EMPTY_INPUT_FAILURE = "EMPTY_INPUT_FAILURE"
    ASYMPTOTIC_TIMEOUT = "ASYMPTOTIC_TIMEOUT"
    RECURSION_DEPTH_EXCEEDED = "RECURSION_DEPTH_EXCEEDED"
    LOGICAL_FLAW = "LOGICAL_FLAW"
    SYNTAX_OR_IMPORT = "SYNTAX_OR_IMPORT"
    MUTATION_SIDE_EFFECT = "MUTATION_SIDE_EFFECT"
    UNKNOWN = "UNKNOWN"


class BugDiagnosis(BaseModel):
    line_number: Optional[int] = None
    bug_type: BugType
    root_cause_explanation: str
    failing_input_summary: str
    suggested_fix: str


class RubricScores(BaseModel):
    correctness_score: float = Field(ge=0.0, le=40.0)      # Max 40
    edge_case_resilience: float = Field(ge=0.0, le=30.0)   # Max 30
    code_quality_and_ast: float = Field(ge=0.0, le=15.0)   # Max 15
    time_complexity_score: float = Field(ge=0.0, le=15.0)  # Max 15

    @property
    def total_score(self) -> float:
        return round(
            self.correctness_score
            + self.edge_case_resilience
            + self.code_quality_and_ast
            + self.time_complexity_score,
            2,
        )


class EvaluationReport(BaseModel):
    problem_id: str
    problem_title: str
    model_name: str
    total_tests: int
    passed_tests: int
    hidden_tests_total: int
    hidden_tests_passed: int
    accuracy_percentage: float
    verdict: str  # ACCEPTED, PARTIAL, REJECTED
    ast_metrics: ASTMetrics
    test_results: List[TestCaseResult]
    diagnoses: List[BugDiagnosis]
    rubric_scores: RubricScores
    generated_at: str
