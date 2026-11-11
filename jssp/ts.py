"""Tabu Search untuk JSSP."""

import random
from typing import Dict, List, Sequence, Tuple

from . import RunResult
from .data import FT06
from .decoder import Evaluator
from .operators import neighbor_swap, random_chromosome

Pair = Tuple[int, int]
Candidate = Tuple[int, Pair, List[int]]


def is_tabu(
    pair: Pair, tabu_list: Dict[Pair, int], iteration: int
) -> bool:
    """Mengembalikan True jika pasangan masih tabu pada iterasi ini."""
    return tabu_list.get(pair, -1) >= iteration


def select_candidate(
    candidates: Sequence[Candidate],
    tabu_list: Dict[Pair, int],
    iteration: int,
    best_makespan: int,
) -> Candidate:
    """Memilih kandidat terbaik yang tidak tabu atau memenuhi aspirasi.

    Jika semua kandidat tabu dan tidak ada yang memenuhi aspirasi, kandidat
    dengan makespan terbaik tetap dipilih.
    """
    if not candidates:
        raise ValueError("Tidak ada kandidat")

    ordered = sorted(candidates, key=lambda item: (item[0], item[1]))
    for candidate in ordered:
        makespan, pair, _ = candidate
        if (not is_tabu(pair, tabu_list, iteration)) or (
            makespan < best_makespan
        ):
            return candidate

    return ordered[0]


def run_ts(
    seed: int,
    budget: int = 3000,
    dataset: Sequence[Sequence[Tuple[int, int]]] = FT06,
    neighbor_count: int = 30,
    tenure: int = 12,
    validate_each: bool = False,
) -> RunResult:
    """Menjalankan Tabu Search dengan 30 tetangga unik per iterasi."""
    rng = random.Random(seed)
    evaluator = Evaluator(
        budget=budget, dataset=dataset, validate_each=validate_each
    )

    n_jobs = len(dataset)
    ops_per_job = len(dataset[0])
    number_of_genes = n_jobs * ops_per_job

    current = random_chromosome(rng, n_jobs, ops_per_job)
    evaluator.evaluate(current)

    tabu_list: Dict[Pair, int] = {}
    iteration = 0

    while evaluator.count < budget:
        iteration += 1
        remaining = budget - evaluator.count
        batch_size = min(neighbor_count, remaining)

        pairs = set()
        attempts = 0
        max_attempts = max(100, batch_size * 100)
        while len(pairs) < batch_size and attempts < max_attempts:
            first, second = rng.sample(range(number_of_genes), 2)
            if current[first] != current[second]:
                pairs.add(
                    (first, second)
                    if first < second
                    else (second, first)
                )
            attempts += 1

        if not pairs:
            break

        best_before_iteration = evaluator.best_makespan
        candidates: List[Candidate] = []
        for pair in sorted(pairs):
            first, second = pair
            neighbor = neighbor_swap(current, first, second)
            makespan = evaluator.evaluate(neighbor)
            candidates.append((makespan, pair, neighbor))

        selected = select_candidate(
            candidates, tabu_list, iteration, best_before_iteration
        )
        selected_makespan, selected_pair, selected_chromosome = selected

        current = selected_chromosome
        tabu_list[selected_pair] = iteration + tenure

    return RunResult(
        method="TS",
        seed=seed,
        evaluator=evaluator,
        iterations=iteration,
    )
