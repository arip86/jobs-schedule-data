"""Baseline pencarian acak untuk JSSP."""

import random
from typing import Sequence, Tuple

from . import RunResult
from .data import FT06
from .decoder import Evaluator
from .operators import random_chromosome


def run_random_search(
    seed: int,
    budget: int = 3000,
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
    validate_each: bool = False,
) -> RunResult:
    """Mengevaluasi sejumlah kromosom acak independen."""
    rng = random.Random(seed)
    evaluator = Evaluator(
        budget=budget, dataset=dataset, validate_each=validate_each
    )

    n_jobs = len(dataset)
    ops_per_job = len(dataset[0])

    for _ in range(budget):
        chromosome = random_chromosome(rng, n_jobs, ops_per_job)
        evaluator.evaluate(chromosome)

    return RunResult(method="acak", seed=seed, evaluator=evaluator)
