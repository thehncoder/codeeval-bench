"""AST Static Analysis & Code Hygiene Analyzer for CodeEval-Bench."""

import ast
from typing import List, Optional
from codeeval.models import ASTMetrics


class ASTAnalyzer:
    """Performs static syntax inspection, complexity metrics, and anti-pattern detection."""

    @classmethod
    def analyze(cls, source_code: str) -> ASTMetrics:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return ASTMetrics(
                syntax_valid=False,
                syntax_error=str(e.msg),
                syntax_error_line=e.lineno,
                has_recursion=False,
                max_loop_nesting=0,
                cyclomatic_complexity=0,
                detected_antipatterns=["Syntax error in submitted code"],
            )

        has_recursion = cls._check_recursion(tree)
        max_loop_nesting = cls._calc_max_loop_nesting(tree)
        cyclomatic = cls._calc_cyclomatic_complexity(tree)
        antipatterns = cls._detect_antipatterns(tree)

        return ASTMetrics(
            syntax_valid=True,
            syntax_error=None,
            syntax_error_line=None,
            has_recursion=has_recursion,
            max_loop_nesting=max_loop_nesting,
            cyclomatic_complexity=cyclomatic,
            detected_antipatterns=antipatterns,
        )

    @classmethod
    def _check_recursion(cls, tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        if isinstance(inner.func, ast.Name) and inner.func.id == func_name:
                            return True
        return False

    @classmethod
    def _calc_max_loop_nesting(cls, tree: ast.AST) -> int:
        max_depth = 0

        def traverse(node: ast.AST, current_depth: int) -> None:
            nonlocal max_depth
            is_loop = isinstance(node, (ast.For, ast.While, ast.AsyncFor))
            new_depth = current_depth + 1 if is_loop else current_depth
            if new_depth > max_depth:
                max_depth = new_depth

            for child in ast.iter_child_nodes(node):
                traverse(child, new_depth)

        traverse(tree, 0)
        return max_depth

    @classmethod
    def _calc_cyclomatic_complexity(cls, tree: ast.AST) -> int:
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.IfExp):
                complexity += 1
        return complexity

    @classmethod
    def _detect_antipatterns(cls, tree: ast.AST) -> List[str]:
        antipatterns: List[str] = []

        for node in ast.walk(tree):
            # Check mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        antipatterns.append(
                            f"Mutable default argument '{type(default).__name__}' at line {node.lineno}"
                        )

            # Check bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    antipatterns.append(f"Bare 'except:' handler at line {node.lineno}")

            # Check eval or exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    antipatterns.append(f"Unsafe dynamic execution '{node.func.id}' at line {node.lineno}")

            # Check global mutations
            if isinstance(node, ast.Global):
                antipatterns.append(f"Global variable mutation statement at line {node.lineno}")

        return antipatterns
