"""Unit tests for AST static analysis and code hygiene detection."""

import pytest
from codeeval.core.ast_analyzer import ASTAnalyzer


def test_valid_syntax():
    code = """
def add(a, b):
    return a + b
"""
    metrics = ASTAnalyzer.analyze(code)
    assert metrics.syntax_valid is True
    assert metrics.syntax_error is None
    assert metrics.cyclomatic_complexity == 1
    assert metrics.has_recursion is False
    assert len(metrics.detected_antipatterns) == 0


def test_syntax_error_detection():
    code = """
def broken(a, b
    return a + b
"""
    metrics = ASTAnalyzer.analyze(code)
    assert metrics.syntax_valid is False
    assert metrics.syntax_error_line is not None
    assert "Syntax error" in metrics.detected_antipatterns[0]


def test_recursion_detection():
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
    metrics = ASTAnalyzer.analyze(code)
    assert metrics.syntax_valid is True
    assert metrics.has_recursion is True


def test_loop_nesting_depth():
    code = """
def triple_loop(matrix):
    total = 0
    for row in matrix:
        for val in row:
            for k in range(val):
                total += k
    return total
"""
    metrics = ASTAnalyzer.analyze(code)
    assert metrics.max_loop_nesting == 3
    assert metrics.cyclomatic_complexity >= 4


def test_antipattern_detection():
    code = """
def dangerous(a, items=[], config={}):
    global counter
    try:
        eval("2 + 2")
    except:
        pass
"""
    metrics = ASTAnalyzer.analyze(code)
    assert metrics.syntax_valid is True
    antipatterns = " ".join(metrics.detected_antipatterns)
    assert "Mutable default argument" in antipatterns
    assert "Bare 'except:'" in antipatterns
    assert "Unsafe dynamic execution 'eval'" in antipatterns
    assert "Global variable mutation" in antipatterns
