"""Simulated Annealing untuk JSSP."""

import math
import random
from typing import Dict, Sequence, Tuple

from . import RunResult
from .data import FT06
from .decoder import Evaluator
from .operators import neighbor_swap, random_chromosome, random_swap_positions


def run_sa(
    seed: int,
    budget: int = 3000,
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
    initial_temperature: float = 100.0,
    alpha: float = 0.997,
    validate_each: bool = False,
) -> RunResult:
    """Menjalankan SA dengan pendinginan per evaluasi."""
    rng = random.Random(seed)
    evaluator = Evaluator(
        budget=budget, dataset=dataset, validate_each=validate_each
    )

    n_jobs = len(dataset)
    ops_per_job = len(dataset[0])

    current = random_chromosome(rng, n_jobs, ops_per_job)
    current_makespan = evaluator.evaluate(current)

    temperatures: Dict[int, float] = {}

    while evaluator.count < budget:
        evaluation_number = evaluator.count + 1
        temperature = initial_temperature * (alpha ** evaluator.count)
        if evaluation_number in (1500, 3000):
            temperatures[evaluation_number] = temperature

        first, second = random_swap_positions(current, rng)
        neighbor = neighbor_swap(current, first, second)
        neighbor_makespan = evaluator.evaluate(neighbor)
        delta = neighbor_makespan - current_makespan

        if delta <= 0 or rng.random() < math.exp(-delta / temperature):
            current = neighbor
            current_makespan = neighbor_makespan

    return RunResult(
        method="SA",
        seed=seed,
        evaluator=evaluator,
        temperatures=temperatures,
    )
