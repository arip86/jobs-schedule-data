"""Package eksperimen Job Shop Scheduling Problem (JSSP)."""

from typing import Any, Dict, Optional


class RunResult:
    """Hasil satu run algoritma beserta statistik tambahan."""

    def __init__(
        self,
        method: str,
        seed: int,
        evaluator: Any,
        generations: Optional[int] = None,
        iterations: Optional[int] = None,
        temperatures: Optional[Dict[int, float]] = None,
    ) -> None:
        self.method = method
        self.seed = seed
        self.evaluator = evaluator
        self.generations = generations
        self.iterations = iterations
        self.temperatures = temperatures if temperatures is not None else {}

    @property
    def best_makespan(self) -> Optional[int]:
        return self.evaluator.best_makespan

    @property
    def best_chromosome(self):
        return self.evaluator.best_chrom
