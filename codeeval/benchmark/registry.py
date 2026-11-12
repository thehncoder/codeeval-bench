"""Registry for loading and querying benchmark problems."""

from typing import Dict, List, Optional
from codeeval.benchmark.dataset.problems import get_all_benchmark_problems
from codeeval.models import Category, Difficulty, Problem


class BenchmarkRegistry:
    """Manages the catalog of benchmark challenge problems."""

    _cache: Optional[Dict[str, Problem]] = None

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._cache is None:
            problems = get_all_benchmark_problems()
            cls._cache = {p.id: p for p in problems}

    @classmethod
    def get_by_id(cls, problem_id: str) -> Optional[Problem]:
        cls._ensure_loaded()
        return cls._cache.get(problem_id)

    @classmethod
    def list_all(cls) -> List[Problem]:
        cls._ensure_loaded()
        return list(cls._cache.values())

    @classmethod
    def filter_problems(
        cls,
        category: Optional[Category] = None,
        difficulty: Optional[Difficulty] = None,
    ) -> List[Problem]:
        cls._ensure_loaded()
        results = list(cls._cache.values())
        if category:
            results = [p for p in results if p.category == category]
        if difficulty:
            results = [p for p in results if p.difficulty == difficulty]
        return results
